import json
from app import app
from datetime import datetime
from flask import Blueprint, request, jsonify, Response
from schema.models import *
from pydantic.fields import FieldInfo
from pydantic import BaseModel
from typing import Any, Union, get_args, get_origin
from api.genomic import genomic
from api.vdjbase import vdjbase
from flask_restx import Resource


api_bp = Blueprint('api_v1', __name__)

def custom_jsonify(obj):
    """Custom JSON encoder for special object types."""

    def encode_obj(o):
        if isinstance(o, Enum):
            return o.value
        if isinstance(o, BaseModel):
            return o.dict()
        if isinstance(o, date):
            return o.isoformat()
        if isinstance(o, dict):
            return {k: encode_obj(v) for k, v in o.items()}
        if isinstance(o, list):
            return [encode_obj(i) for i in o]
        return o
    
    return Response(
        json.dumps(encode_obj(obj)),
        mimetype='application/json'
    )


"""Get species list based on type."""

@api_bp.route('/<type>/species', methods=['GET'])
def get_species(type):
    """Get species list based on type."""
    species_api = genomic.SpeciesApi(Resource)
    species_list = species_api.get()
    species_response_obj = []
    for item in species_list:
        ontology_obj = Ontology(label=item)
        species_response_obj.append(ontology_obj)

    species_response_obj = SpeciesResponse(species=species_response_obj)
    try:
        return jsonify(species_response_obj.dict()), 200

    except Exception as e:
        error_response = ErrorResponse(message=str(e))
        return jsonify(error_response.dict()), 500


@api_bp.route('/<type>/datasets/<species>', methods=['GET'])
def get_species_datasets(type, species):
    """Get datasets for a species based on type."""
    data_sets = None
    if type == "genomic":
        data_sets = genomic.DataSetAPI(Resource)
        data_sets = data_sets.get(species)

    elif type == "airrseq":
        data_sets = vdjbase.DataSetAPI(Resource)
        data_sets = data_sets.get(species)

    else:
        error_response = ErrorResponse(message="type not exists")
        return jsonify(error_response.dict()), 500

    data_set_list = []
    for data_set in data_sets:
        data_set_obj = Dataset(dataset=data_set["dataset"], locus=data_set["locus"] if type == "genomic" else None, type=type)
        data_set_list.append(data_set_obj)

    data_set_response = DatasetsResponse(datasets=data_set_list)
    try:
        return jsonify(data_set_response.dict()), 200

    except Exception as e:
        error_response = ErrorResponse(message=str(e))
        return jsonify(error_response.dict()), 500


@api_bp.route('/<type>/subjects/<species>/<dataset>', methods=['GET'])
def get_subject_datasets(type, species, dataset):
    """Get subject datasets for a species and dataset based on type."""
    if type == "genomic":
        try:
            subjects_list = genomic.SubjectsAPI(Resource)
            subjects_list = subjects_list.get(species, dataset)
            dataset_list = []
            for sample in subjects_list.get('samples'):
                subject_identifier = sample['sample_name'].split('_')[0:1]
                subject_identifier = '_'.join(sample['sample_name'].rsplit('_', 1)[:-1])

                subject_dataset_obj = SubjectDataset(id=sample['sample_id'], 
                                                     study_name=sample['study_name'], 
                                                     subject_identifier=subject_identifier, 
                                                     sample_identifier=sample['sample_name'],
                                                     dataset=sample['dataset'])
                dataset_list.append(subject_dataset_obj)
            subject_dataset_response_obj = SubjectDatasetResponse(subject_datasets=dataset_list)
          
            try:
                return jsonify(subject_dataset_response_obj.dict()), 200

            except Exception as e:
                error_response = ErrorResponse(message=str(e))
                return jsonify(error_response.dict()), 500

        except Exception as e:
            error_response = ErrorResponse(message=str(e))
            return jsonify(error_response.dict()), 500

    elif type == "airrseq":
        try:
            subjects_list = vdjbase.SamplesApi(Resource)
            request.args = {'cols': '["sample_name", "study_id", "subject_id"]'}
            subjects_list = subjects_list.get(species, dataset)
            dataset_list = []
            for sample in subjects_list.get('samples'):
                subject_dataset_obj = SubjectDataset(id=sample['sample_name'], 
                                                     study_name=sample['study_id'], 
                                                     subject_identifier=sample['subject_id'], 
                                                     sample_identifier=sample['sample_id'],
                                                     dataset=sample['dataset'])
                dataset_list.append(subject_dataset_obj)
            subject_dataset_response_obj = SubjectDatasetResponse(subject_datasets=dataset_list)
          
            try:
                return jsonify(subject_dataset_response_obj.dict()), 200

            except Exception as e:
                error_response = ErrorResponse(message=str(e))
                return jsonify(error_response.dict()), 500
        
        except Exception as e:
            error_response = ErrorResponse(message=str(e))
            return jsonify(error_response.dict()), 500


@api_bp.route('/<type>/sample_genotype/<species>/<dataset>/<subject>/<sample>', methods=['GET'])
def get_sample_genotype(type, species, dataset, subject, sample):
    genotype_object = Genotype(receptor_genotype_id='',
                                   locus=Locus('IGH'),
                                   documented_alleles=None,
                                   undocumented_alleles=None,
                                   deleted_genes=None,
                                   inference_process=None)
    
    if type == "genomic":
        return custom_jsonify(genotype_object.dict()), 200

    elif type == "airrseq":
        return custom_jsonify(genotype_object.dict()), 200

    else:
        error_response = ErrorResponse(message=str("type not  exists"))
        return jsonify(error_response.dict()), 500
    

@api_bp.route('/<type>/sample_metadata/<species>/<dataset>/<subject>/<sample>', methods=['GET'])
def get_sample_metadata(type, species, dataset, subject, sample):
    """Get metadata for a specific sample."""
    if type == "genomic":
        try:
            subject_info = genomic.SubjectInfoApi(Resource)
            subject_info = subject_info.get(species, dataset, sample)
            rep_obj = SampleMetadataResponse(Repertoire=create_repertoire_obj(subject_info))
            return custom_jsonify(rep_obj.dict()), 200

        except Exception as e:
            error_response = ErrorResponse(message=str(subject_info))
            return jsonify(error_response), 500
        
    elif type == "airrseq":
        try:
            subject_info = vdjbase.SampleInfoApi(Resource)
            subject_info = subject_info.get(species, dataset, sample)
            rep_obj = SampleMetadataResponse(Repertoire=create_repertoire_obj(subject_info))
            return custom_jsonify(rep_obj.dict()), 200

        except Exception as e:
            error_response = ErrorResponse(message=str(subject_info))
            return jsonify(error_response), 500
    else:
        error_response = ErrorResponse(message=str("type not  exists"))
        return jsonify(error_response.dict()), 500


def create_repertoire_obj(subject_info):
    """Create a Repertoire object from subject information."""
    subject_info = fill_missing_required_fields(Repertoire,  subject_info)

    rep_object = Repertoire(repertoire_id=subject_info.get("repertoire_id", None),
                            repertoire_name=subject_info.get("repertoire_name", None),
                            repertoire_description=subject_info.get("repertoire_description", None),
                            study=create_study_object(subject_info),
                            subject=create_subject_objects(subject_info),
                            sample=create_sample_processing_list(subject_info),
                            data_processing=create_data_processing_list(subject_info))
    
    return rep_object


def create_data_processing_list(subject_info):
    """Create a list of DataProcessing objects from subject information."""
    subject_info = fill_missing_required_fields(DataProcessing,  subject_info)

    data_processing_list = []
    data_processing_obj = DataProcessing(data_processing_id=subject_info.get("data_processing_id"),
                                         primary_annotation=subject_info.get("primary_annotation"),
                                         software_versions=subject_info.get("software_versions"),
                                         paired_reads_assembly=subject_info.get("paired_reads_assembly"),
                                         quality_thresholds=subject_info.get("quality_thresholds"),
                                         primer_match_cutoffs=subject_info.get("primer_match_cutoffs"),
                                         collapsing_method=subject_info.get("collapsing_method"),
                                         data_processing_protocols=subject_info.get("data_processing_protocols"),
                                         data_processing_files=[subject_info.get("data_processing_files")] if subject_info.get("data_processing_files") is not None else None,
                                         germline_database=subject_info.get("germline_database"),
                                         germline_set_ref=subject_info.get("germline_set_ref"),
                                         analysis_provenance_id=subject_info.get("analysis_provenance_id"))
    
    data_processing_list.append(data_processing_obj)
    return data_processing_list
    

def create_sample_processing_list(subject_info):
    """Create a list of SampleProcessing objects from subject information."""
    subject_info = fill_missing_required_fields(Sample,  subject_info)
    subject_info = fill_missing_required_fields(CellProcessing,  subject_info)
    subject_info = fill_missing_required_fields(NucleicAcidProcessing,  subject_info)
    subject_info = fill_missing_required_fields(SequencingRun,  subject_info)

    try:
        library_generation_method = LibraryGenerationMethod(subject_info.get("library_generation_method"))
    except:
        library_generation_method = LibraryGenerationMethod("other")

    sample_processing_list = []
    sample_processing_obj = SampleProcessing(sample_processing_id=subject_info.get("sample_processing_id", None),
                                             sample_id=subject_info.get("sample_id"),
                                             sample_type=subject_info.get("sample_type"),
                                             tissue=Ontology(id=subject_info.get("tissue_id", ""), lable=subject_info.get("tissue_label", "")),
                                             anatomic_site=subject_info.get("anatomic_site"),
                                             disease_state_sample=subject_info.get("disease_state_sample"),
                                             collection_time_point_relative=subject_info.get("collection_time_point_relative"),
                                             collection_time_point_relative_unit=Ontology(id=subject_info.get("collection_time_point_relative_unit_id", ""), lable=subject_info.get("collection_time_point_relative_unit_label", "")),
                                             collection_time_point_reference=subject_info.get("collection_time_point_reference"),
                                             biomaterial_provider=subject_info.get("biomaterial_provider"),
                                             tissue_processing=subject_info.get("tissue_processing"),
                                             cell_subset=Ontology(id=subject_info.get("cell_subset_id", ""), lable=subject_info.get("cell_subset_label", "")),
                                             cell_phenotype=subject_info.get("cell_phenotype"),
                                             cell_species=Ontology(id=subject_info.get("cell_species_id", ""), lable=subject_info.get("cell_species_label", "")),
                                             single_cell=str_to_bool((subject_info.get("single_cell"))),
                                             cell_number=subject_info.get("cell_number") if subject_info.get("cell_number") != '' else 0,
                                             cells_per_reaction=subject_info.get("cells_per_reaction") if subject_info.get("cells_per_reaction") != '' else 0,
                                             cell_storage=str_to_bool(subject_info.get("cell_storage")),
                                             cell_quality=subject_info.get("cell_quality"),
                                             cell_isolation=subject_info.get("cell_isolation"),
                                             cell_processing_protocol=subject_info.get("cell_processing_protocol"),
                                             template_class=TemplateClass(subject_info.get("template_class").upper()),
                                             template_quality=subject_info.get("template_quality"),
                                             template_amount=subject_info.get("template_amount"),
                                             template_amount_unit=Ontology(id=subject_info.get("template_amount_unit_id", ""), lable=subject_info.get("template_amount_unit_label", "")),
                                             library_generation_method=library_generation_method,
                                             library_generation_protocol=subject_info.get("library_generation_protocol"),
                                             library_generation_kit_version=subject_info.get("library_generation_kit_version"),
                                             pcr_target=subject_info.get("pcr_target"),
                                             complete_sequences=create_complete_sequences_enum(subject_info),
                                             physical_linkage=PhysicalLinkage(subject_info.get("physical_linkage")),
                                             sequencing_run_id=subject_info.get("sequencing_run_id"),
                                             total_reads_passing_qc_filter=subject_info.get("total_reads_passing_qc_filter"),
                                             sequencing_platform=subject_info.get("sequencing_platform"),
                                             sequencing_facility=subject_info.get("sequencing_facility"),
                                             sequencing_run_date=subject_info.get("sequencing_run_date"),
                                             sequencing_kit=subject_info.get("sequencing_kit"),
                                             sequencing_files=create_sequencing_data_object(subject_info)
                                             )
    
    sample_processing_list.append(sample_processing_obj)

    return sample_processing_list

def create_complete_sequences_enum(subject_info):
    """Create a CompleteSequences enum from subject information."""
    try:
        return CompleteSequences(subject_info.get("complete_sequences"))
    except:
        return CompleteSequences("partial")


def create_sequencing_data_object(subject_info):
    """Create a SequencingData object from subject information."""
    subject_info = fill_missing_required_fields(SequencingData,  subject_info)

    sequencing_data_obj = SequencingData(sequencing_data_id=subject_info.get("sequencing_data_id") if subject_info.get("sequencing_data_id") is not None else "",
                                         file_type=FileType(field_value=None),
                                         filename = subject_info.get("filename"),
                                         read_direction = ReadDirection(field_value=None),
                                         read_length = subject_info.get("read_length"),
                                         paired_filename = subject_info.get("paired_filename"),
                                         paired_read_direction = PairedReadDirection(field_value=None),
                                         paired_read_length = subject_info.get("paired_read_length"),
                                         index_filename = subject_info.get("index_filename"),
                                         index_length = subject_info.get("index_length"),
                                        )
    
    return sequencing_data_obj


def str_to_bool(value):
    """Convert a string to a boolean."""
    if isinstance(value, str):
        return value.lower() == 'true'
    return bool(value)


def create_subject_objects(subject_info):
    """Create Subject objects from subject information."""
    subject_info = fill_missing_required_fields(Subject,  subject_info)

    subject_object = Subject(subject_id=subject_info.get("subject_id"),
                             synthetic=subject_info.get("synthetic"),
                             species=Ontology(id=subject_info.get("species_id", ""), lable=subject_info.get("species_label", "")),
                             organism=Ontology(id=subject_info.get("organism_id", ""), lable=subject_info.get("organism_label", "")), 
                             sex=Sex(field_value=create_Sex_Enum(subject_info)),
                             age_min=subject_info.get("age_min"),
                             age_max=subject_info.get("age_max"),
                             age_unit=Ontology(id=subject_info.get("age_unit_id", ""), lable=subject_info.get("age_unit_label", "")),
                             age_event=subject_info.get("age_event"),
                             age=subject_info.get("age"),
                             ancestry_population=subject_info.get("ancestry_population"),
                             ethnicity=subject_info.get("ethnicity"),
                             race=subject_info.get("race", None),
                             strain_name=subject_info.get("strain_name", None),
                             linked_subjects=subject_info.get("linked_subjects", None),
                             link_type=subject_info.get("link_type", None),
                             diagnosis=create_diagnosis_list(subject_info),
                             genotype=create_subject_genotype_obj(subject_info))

    return subject_object


def create_Sex_Enum(subject_info):
    """Create a Sex enum from subject information."""
    try:
        return SexEnum(subject_info.get("sex"))
    except:
        return None


def create_subject_genotype_obj(subject_info):
    """Create a SubjectGenotype object from subject information."""
    subject_genotype_obj = SubjectGenotype(receptor_genotype_set=GenotypeSet(receptor_genotype_set_id=subject_info.get("receptor_genotype_set_id") if subject_info.get("receptor_genotype_set_id") is not None else "",
                                                                             genotype_class_list=create_genotype_model_list(subject_info)))
    return subject_genotype_obj


def create_genotype_model_list(subject_info):
    """Create a list of GenotypeModel objects from subject information."""
    # genotype_model_list = []
    # genotype_model_obj = GenotypeModel(receptor_genotype_id=)
    return None


def create_diagnosis_list(subject_info):
    """Create a list of Diagnosis objects from subject information."""
    subject_info = fill_missing_required_fields(Diagnosis,  subject_info)

    diagnosis_list = []
    diagnosis_object = Diagnosis(study_group_description=subject_info.get("study_group_description"),
                                 disease_diagnosis=Ontology(id=subject_info.get("disease_diagnosis_id", ""), lable=subject_info.get("disease_diagnosis_label", "")),
                                 disease_length=subject_info.get("disease_length"),
                                 disease_stage=subject_info.get("disease_stage"),
                                 prior_therapies=subject_info.get("prior_therapies"),
                                 immunogen=subject_info.get("immunogen"),
                                 intervention=subject_info.get("intervention"),
                                 medical_history=subject_info.get("medical_history"))
    diagnosis_list.append(diagnosis_object)
    return diagnosis_list


def create_study_object(subject_info):
    """Create a Study object from subject information."""
    subject_info = fill_missing_required_fields(Study,  subject_info)

    study_object = Study(study_id=subject_info.get("study_id"),
                         study_title=subject_info.get("study_title"),
                         study_type=Ontology(id=subject_info.get("study_type_id"), label=subject_info.get("study_type_lable")),
                         study_description=subject_info.get("study_description", None),
                         inclusion_exclusion_criteria=subject_info.get("inclusion_exclusion_criteria", ""),
                         grants=subject_info.get("grants", ""),
                         study_contact=subject_info.get("study_contact", None),
                         collected_by=subject_info.get("collected_by", ""),
                         lab_name=subject_info.get("lab_name", ""),
                         lab_address=subject_info.get("lab_address", ""),
                         submitted_by=subject_info.get("submitted_by", ""),
                         pub_ids=subject_info.get("pub_ids", ""),
                         keywords_study=create_keyword_study_list(subject_info), ###
                         adc_publish_date=create_date(subject_info, "adc_publish_date"),
                         adc_update_date=create_date(subject_info, "adc_update_date"),
                         )
    return study_object


def create_keyword_study_list(subject_info):
    """Create a list of KeywordsStudyEnum from subject information."""
    return [KeywordsStudyEnum('contains_ig')]


def create_date(subject_info, field):
    """Create a datetime object from subject information and field."""
    if subject_info.get(field) == "":
        return None
    
    else:
        return datetime.now()

def get_default_value(field_type: Any) -> Any:
    """
    Get the default value for a given field type.
    
    Args:
        field_type: The type of the field.
    
    Returns:
        The default value for the field type.
    """
    try:
        if get_origin(field_type) is Union:
            args = get_args(field_type)
            field_type = args[0] if args[1] is type(None) else args[1]

        if field_type == 'int':
            return 0
        elif field_type == 'float':
            return 0.0
        elif field_type == 'str':
            return ""
        elif field_type == 'bool':
            return False
        elif field_type == 'list':
            return []
        elif field_type == 'dict':
            return {}
        elif field_type == 'datetime':
            return datetime.now()
        elif field_type == 'date':
            return datetime.now()
        elif 'Optional' in field_type:
            pass
        else:
            if issubclass(globals()[field_type] , Enum):
                # Get the first value of the Enum
                return next(iter(globals()[field_type])).value
    
    except:
        pass

    return None


def fill_missing_required_fields(model_cls: BaseModel, data: dict) -> dict:
    """
    Fill missing required fields in the given data with default values.
    
    Args:
        model_cls: The Pydantic model class.
        data: The data dictionary.
    
    Returns:
        The data dictionary with missing required fields filled.
    """
    filled_data = data.copy()

    for field_name, field_info in model_cls.__fields__.items():
        if field_name in data:
            if is_required(field_info):
                field_type = model_cls.__annotations__[field_name]
                if data[field_name] is None or (field_type != 'str' and data[field_name] == ''):
                    if field_type != 'List[KeywordsStudyEnum]':
                        default_value = get_default_value(field_type)
                    if default_value is not None:
                        filled_data[field_name] = default_value

    return filled_data

def is_required(field_info: FieldInfo) -> bool:
    """
    Check if a field is required.
    
    Args:
        field_info: The field information.
    
    Returns:
        Boolean indicating if the field is required.
    """
    if 'required=True' in str(field_info):
        return True
    
    return False