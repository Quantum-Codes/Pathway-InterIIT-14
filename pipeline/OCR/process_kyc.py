import pathway as pw

from google.api_core.client_options import ClientOptions
from google.cloud import documentai_v1
import boto3
import cv2, os, random, logging, json, sys, re, string
from pathlib import Path
from dotenv import load_dotenv
import numpy as np
from pdf2image import convert_from_path # Requires Poppler installation
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from relevant_images.pathway_workflow_custom import CustomPathwayWorkflow

load_dotenv()

# aws config
AWS_BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME", "amzn-s3-pathway-bucket")
AWS_PROFILEPIC_BUCKET = os.environ.get("AWS_PROFILEPIC_BUCKET", "amzn-s3-pathway-profilepic")
SOURCE_PREFIX = "forms/pending/" 
DESTINATION_LOCAL_PATH = Path("out/kyc_pdfs/").resolve()
DESTINATION_LOCAL_PATH.mkdir(parents=True, exist_ok=True)
AWS_REGION = os.environ.get("AWS_REGION", "eu-north-1")
S3_PATH_STYLE = False

AWS_ACCESS_KEY_ID = os.environ["AWS_ACCESS_KEY_ID"]
AWS_SECRET_ACCESS_KEY = os.environ["AWS_SECRET_ACCESS_KEY"]

S3_FULL_PATH = f"s3://{AWS_BUCKET_NAME}/{SOURCE_PREFIX}"

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("pathway_pipeline")

# kafka topics
MAIN_BACKEND_TOPIC = os.getenv("MAIN_BACKEND_TOPIC", "entities")

PROCESSOR_NAME = os.environ["PROCESSOR_NAME"]  # e.g., "projects/123456789/locations/us/processors/processor_id"
SERVICE_ACCOUNT_FILE = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]  # path to service account json file

s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

allowed_chars = string.ascii_letters + string.digits + string.whitespace + string.punctuation
pattern_str = f"[^{re.escape(allowed_chars)}]"
cleanup_pattern = re.compile(pattern_str)

opts = ClientOptions(api_endpoint ="us-documentai.googleapis.com")
client = documentai_v1.DocumentProcessorServiceClient(client_options=opts)
request = documentai_v1.GetProcessorRequest(name=PROCESSOR_NAME)
processor = client.get_processor(request=request)

rdkafka_settings = {
    "bootstrap.servers": os.environ.get("BOOTSTRAP_SERVERS", "localhost:9092"),
    "group.id": os.environ.get("GROUP_ID", "0"),
    "session.timeout.ms": os.environ.get("SESSION_TIMEOUT_MS", "6000"),
    "auto.offset.reset": os.environ.get("AUTO_OFFSET_RESET", "earliest"),
}
@pw.udf
def upload_image_to_s3(local_path: str) -> str:
    filename = os.path.basename(local_path)
    s3_key = f"profilepics/{filename}"

    s3.upload_file(local_path, AWS_PROFILEPIC_BUCKET, s3_key)

    return f"https://{AWS_PROFILEPIC_BUCKET}.s3.{AWS_REGION}.amazonaws.com/{s3_key}"

@pw.udf
def save_pdf(binary_data: bytes, s3_key: str) -> str:
    """
    Takes binary bytes (from S3) and the S3 key (metadata),
    saves the file locally as a PDF,
    and returns the local file path.
    """

    cleaned = s3_key.strip('"')

    # Extract filename from S3 key
    filename = os.path.basename(cleaned)
    local_path = DESTINATION_LOCAL_PATH / filename
    # Write the PDF file
    with open(local_path, "wb") as f:
        f.write(binary_data)

    # Return the final local path
    return str(local_path)



@pw.udf
def crop_faces_from_pdf(pdf_path: str, name: str) -> list[str]:
    """
    Detects and crops faces from every page of a PDF file.

    Args:
        pdf_path (str): Path to the input PDF file.
    
    Returns:
        list: A list of paths to the saved face image files.
    """
    out_dir = Path("faces")
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        pages = convert_from_path(pdf_path, dpi=300)
    except Exception as e:
        print(f"Error converting PDF. Check Poppler installation/path. Details: {e}")
        return []

    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    
    all_cropped_pics = []
    face_count = 0

    for page_num, pil_image in enumerate(pages, start=1):
        img_rgb = np.array(pil_image)
        img = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(80,80))
        
        for i, (x,y,w,h) in enumerate(faces, start=1):
            face_count += 1
            crop = img[y:y+h, x:x+w]
            
            # Create a unique filename based on the original file and page/face index
            pdf_stem = Path(pdf_path).stem
            # out_file = out_dir / f"{pdf_stem}_p{page_num}_face{i}.jpg"
            out_file = out_dir / f"{name.replace(' ', '_')}_{i}.jpg"
            
            cv2.imwrite(str(out_file), crop)
            all_cropped_pics.append(str(out_file))


    # cleanup pdf
    try:
        os.remove(pdf_path)
    except Exception as e:
        log.warning(f"Could not delete temp pdf {pdf_path}. Details: {e}")

    return all_cropped_pics


@pw.udf
def process_form_fields(file_path: str) -> dict:
    # form fields

    # # caching mechanism
    # if Path(f"./out/kyc_cache/{Path(file_path).stem}_fields.json").exists():
    #     log.info(f"Cache HIT for {file_path}, loading cached fields.")
    #     with open(f"./out/kyc_cache/{Path(file_path).stem}_fields.json", "r") as f:
    #         cached_fields = json.load(f)
    #     log.info(f"Loaded cached fields for {file_path}")
    #     return cached_fields
    
    log.info(f"Started field processing for {file_path}")

    fields = { # updated full list of fields we can extract. Already updated the GCP fieldlist.
        "annual_income": "", # new field
        "applicant_email": "", # new field
        "applicant_first_name": "",
        "applicant_last_name": "",
        "applicant_middle_name": "",
        "applicant_mobile_number": "", # new field
        "applicant_name_prefix": "",
        "current_address": "", # CHANGED from address to current_address
        "date_of_birth": "",
        "father_first_name": "",
        "father_last_name": "",
        "father_middle_name": "",
        "father_name_prefix": "",
        "gender": "",
        "marital_status": "", # new field
        "mother_first_name": "",
        "mother_last_name": "",
        "mother_middle_name": "",
        "mother_name_prefix": "",
        "nationality": "", # new field
        "occupation": "", # new field
        "passport_number": "", # new field
        "permanent_address": "", # new field
        "residential_status": "",
        "sources_of_income": [], # new field - LIST LIST LIST LIST
        "unique_identification_number": "" # new field
    }
    # Read the file.
    with open(file_path, "rb") as image:
        image_content = image.read()
    # For supported MIME types, refer to https://cloud.google.com/document-ai/docs/file-types
    raw_document = documentai_v1.RawDocument(
        content=image_content,
        mime_type="application/pdf",
    )

    request = documentai_v1.ProcessRequest(name=processor.name, raw_document=raw_document)
    document = client.process_document(request=request).document
    # For a full list of `Document` object attributes, reference this page:
    # https://cloud.google.com/document-ai/docs/reference/rest/v1/Document

    fields.update({entity.type_: entity.mention_text for entity in document.entities})
    
    # we extract parts of names separately then join together so we are able to get all parts of the name correctly and not just end up with the first name when we try to extract just "applicant_name"
    applicant_name_parts = [fields.pop("applicant_first_name"), fields.pop("applicant_middle_name"), fields.pop("applicant_last_name")]
    father_name_parts = [fields.pop("father_first_name"), fields.pop("father_middle_name"), fields.pop("father_last_name")]
    mother_name_parts = [fields.pop("mother_first_name"), fields.pop("mother_middle_name"), fields.pop("mother_last_name")]
    # remove empty parts so no duplicate space problem
    applicant_name_parts = [item for item in applicant_name_parts if item]
    father_name_parts = [item for item in father_name_parts if item]
    mother_name_parts = [item for item in mother_name_parts if item]
    # add combined
    fields["applicant_name"] = " ".join(applicant_name_parts)
    fields["father_name"] = " ".join(father_name_parts)
    fields["mother_name"] = " ".join(mother_name_parts)
    log.info(f"Processed KYC form fields of {fields['applicant_name']}")

    # ALL FIELDS IN THE GCP EXTRACTOR ARE MARKED AS STRING. one datetime also returns string as YYYY-MM-DD
    def remove_emojis(text: str) -> str:
        return cleanup_pattern.sub("", text)
    
    def clean_field(value: str | list[str]) -> str | list[str]:
        if isinstance(value, str):
            return remove_emojis(value).strip().lower()
        elif isinstance(value, list):
            return [remove_emojis(item).strip().lower() for item in value] # guaranteed all list items are str
        return value
    
    fields = {k: clean_field(v) for k, v in fields.items()}

    # save to cache
    Path("./out/kyc_cache").mkdir(parents=True, exist_ok=True)
    with open(f"./out/kyc_cache/{Path(file_path).stem}_fields.json", "w") as f:
        json.dump(fields, f, indent=2)
    log.info(f"Saved cached fields for {file_path}")
    return fields

def _extract_person_name(file_path: str) -> str:
        """
        Extract person name from filename.
        
        Example: 'john_doe.jpg' → 'John Doe'
        """
        filename = Path(file_path).stem
        return filename.replace('_', ' ').title()

@pw.udf
def match_face_for_links(paths: list[str]) -> list[str]:    
    # Initialize with list of face image paths
    workflow = CustomPathwayWorkflow(face_image_paths=paths)
    
    # Extract person name from the first path for search
    first_path = paths[0]
    person_name = _extract_person_name(first_path)
    
    # Process query images with Google Image Search
    source_urls = workflow.run(
        input_folder="input", 
        cleanup=True,
        search_keyword=person_name,
        num_results=10
    )

    # remove all files from paths
    for img_path in paths:
        try:
            os.remove(img_path)
        except Exception as e:
            log.warning(f"Could not delete temp image {img_path}. Details: {e}")
    
    # Returns list of source page URLs
    return source_urls

# Define the schema for the KYC database entries
class KYCDBSchema(pw.Schema):
    data: bytes

files = pw.io.s3.read(
    path=S3_FULL_PATH,
    format="binary",
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region=AWS_REGION,
    s3_path_style=S3_PATH_STYLE,
    with_metadata=True,
    mode="streaming"
)

raw_s3_key = files._metadata["path"]             # Json → Pathway Json column
s3_key = pw.apply(lambda x: str(x), raw_s3_key)  # Convert to Python str


saved = files.select(
    path=save_pdf(pw.this.data, s3_key),
    s3_key=s3_key
)


results = saved.select(
    path = pw.this.path,
    fields = process_form_fields(pw.this.path),
)

results = results.select(
    pics = crop_faces_from_pdf(saved.path, pw.this.fields["applicant_name"].to_string()),
    fields = pw.this.fields,
)

results = results.with_columns(
    profile_pic = upload_image_to_s3(pw.this.pics[0])
)

@pw.udf
def random_id(name: str) -> str:
    return str(random.randint(1,1000))

# ALL STILL STRINGS
results = results.select(
    entity_id = random_id(pw.this.fields["applicant_name"]), # simulate row ID or user ID we would have in a real DB
    profile_pic = pw.this.profile_pic,
    face_match_urls = match_face_for_links(pw.this.pics),
    applicant_name = pw.this.fields["applicant_name"],
    date_of_birth = pw.this.fields["date_of_birth"],
    gender = pw.this.fields["gender"],
    father_name = pw.this.fields["father_name"],
    mother_name = pw.this.fields["mother_name"],
    residential_status = pw.this.fields["residential_status"],
    annual_income = pw.this.fields["annual_income"],
    applicant_email = pw.this.fields["applicant_email"],
    applicant_mobile_number = pw.this.fields["applicant_mobile_number"],
    marital_status = pw.this.fields["marital_status"],
    current_address = pw.this.fields["current_address"],
    nationality = pw.this.fields["nationality"],
    occupation = pw.this.fields["occupation"],
    passport_number = pw.this.fields["passport_number"],
    permanent_address = pw.this.fields["permanent_address"],
    sources_of_income = pw.this.fields["sources_of_income"],
    unique_identification_number = pw.this.fields["unique_identification_number"],
)

# main.py not using all info provided though
pw.io.kafka.write(results, rdkafka_settings, topic_name=MAIN_BACKEND_TOPIC, format="json")

# WITH THE NEW FORMAT
pw.io.jsonlines.write(
    results,
    "./out/ocr_results.jsonl",
)
pw.run(monitoring_level=pw.MonitoringLevel.NONE)


# All fields:

"""
entity_id 
face_match_urls 
applicant_name 
date_of_birth 
gender 
father_name 
mother_name 
residential_status 
annual_income 
applicant_email 
applicant_mobile_number 
marital_status 
current_address 
nationality 
occupation 
passport_number 
permanent_address 
sources_of_income 
unique_identification_number 
"""