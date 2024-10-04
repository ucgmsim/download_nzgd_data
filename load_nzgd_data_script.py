"""
Script to load NZGD data and convert to a standard format
"""
import numpy as np
from pathlib import Path
import toml
import loading_funcs_for_nzgd_data
import xlrd
from tqdm import tqdm
import natsort

output_dir = Path("/home/arr65/data/nzgd/standard_format_batch1/cpt")

parquet_output_dir = output_dir / "data"
metadata_output_dir = output_dir / "metadata"

parquet_output_dir.mkdir(exist_ok=True, parents=True)
metadata_output_dir.mkdir(exist_ok=True, parents=True)

downloaded_files = Path("/home/arr65/data/nzgd/downloaded_files/cpt")

meta_successfully_loaded = []
meta_failed_to_load = []
meta_ags_failed_to_load = []
meta_xls_failed_to_load = []

record_counter = 0

#previously_converted_filenames = list(np.loadtxt("/home/arr65/data/nzgd/standard_format_batch1/cpt/metadata/successfully_loaded.txt", dtype=str))
previously_converted_filenames = []

previously_converted_records = []
for filename in previously_converted_filenames:
    file_name_parts = filename.split("_")
    previously_converted_records.append(f"{file_name_parts[0]}_{file_name_parts[1]}")

#records_to_convert = [x for x in list(downloaded_files.glob("*")) if x.name not in previously_converted_records]
records_to_convert = []
for record_dir in natsort.natsorted(list(downloaded_files.glob("*"))):
    if record_dir.name not in previously_converted_records:
        records_to_convert.append(record_dir)

for record_dir in tqdm(records_to_convert):
#for record_dir in [Path("/home/arr65/data/nzgd/downloaded_files/cpt/CPT_12402")]:

    has_loaded_a_file_for_this_record = False

    ags_file_load_attempted = False
    xls_file_load_attempted = False

    ags_load_failed = False
    xls_load_failed = False

    record_counter += 1
    if record_counter % 100 == 0:
        np.savetxt(metadata_output_dir / "successfully_loaded.txt", np.array(meta_successfully_loaded), fmt="%s",
                   header="successfully_loaded_files")
        np.savetxt(metadata_output_dir / "failed_to_load.txt", np.array(meta_failed_to_load), fmt="%s",
                   header="record_name, file_name, error_message")
        np.savetxt(metadata_output_dir / "ags_failed_to_load.txt", np.array(meta_ags_failed_to_load), fmt="%s",
                   header="record_name, file_name, error_message")
        np.savetxt(metadata_output_dir / "xls_failed_to_load.txt", np.array(meta_xls_failed_to_load), fmt="%s",
                   header="record_name, file_name, error_message")

    ### Skip this record if the only available files are pdf
    if len(list(record_dir.glob("*.pdf"))) == len(list(record_dir.glob("*"))):
        meta_failed_to_load.append(f"{record_dir.name}, N/A, only_pdf_files_are_available")

    ### ags files
    files_to_try = list(record_dir.glob("*.ags")) + list(record_dir.glob("*.AGS"))
    if len(files_to_try) > 0:
        for file_to_try in files_to_try:
            try:
                ags_file_load_attempted = True
                record_df = loading_funcs_for_nzgd_data.load_ags(file_to_try)
                record_df.insert(0,"record_name",record_dir.name)
                record_df.reset_index(inplace=True, drop=True)
                record_df.attrs["original_file_name"] = file_to_try.name
                record_df.to_parquet(parquet_output_dir / f"{record_dir.name}.parquet")
                meta_successfully_loaded.append(file_to_try.name)

                has_loaded_a_file_for_this_record = True
                continue

            ## If the ags file is missing data, KeyError or UnboundLocalError will be raised
            except(KeyError, UnboundLocalError) as e:
                meta_ags_failed_to_load.append(f"{record_dir.name}, {file_to_try.name}, {str(e).replace(',',';')}")
                ags_load_failed = True
                pass

    if has_loaded_a_file_for_this_record:
        continue

    ### xls files
    files_to_try = list(record_dir.glob("*.xls")) + list(record_dir.glob("*.XLS")) + \
                   list(record_dir.glob("*.xlsx")) + list(record_dir.glob("*.XLSX"))

    if len(files_to_try) > 0:
        for file_to_try in files_to_try:
            try:
                xls_file_load_attempted = True
                record_df = loading_funcs_for_nzgd_data.load_cpt_xls_file(file_to_try)
                record_df.attrs["original_file_name"] = file_to_try.name
                record_df.insert(0,"record_name",record_dir.name)
                record_df.reset_index(inplace=True, drop=True)
                record_df.to_parquet(parquet_output_dir / f"{record_dir.name}.parquet")
                meta_successfully_loaded.append(file_to_try.name)
                has_loaded_a_file_for_this_record = True
                continue

            except(ValueError, xlrd.compdoc.CompDocError, Exception) as e:
                meta_xls_failed_to_load.append(f"{record_dir.name}, {file_to_try.name}, {e}")
                pass
                xls_load_failed = True

    if (not ags_file_load_attempted) and (not xls_file_load_attempted):
        meta_failed_to_load.append(f"{record_dir.name}, N/A, Did_not_attempt_to_load_any_files")

    if ags_load_failed and xls_load_failed:
        meta_failed_to_load.append(f"{record_dir.name}, N/A, Both_ags_and_xls_load_failed")

    if ags_load_failed and (not xls_file_load_attempted):
        meta_failed_to_load.append(f"{record_dir.name}, {file_to_try.name}, ags_load_failed")

    if xls_load_failed and (not ags_file_load_attempted):
        meta_failed_to_load.append(f"{record_dir.name}, {file_to_try.name}, xls_load_failed")




np.savetxt(metadata_output_dir / "successfully_loaded.txt", np.array(meta_successfully_loaded), fmt="%s",header="successfully_loaded_files")
np.savetxt(metadata_output_dir / "failed_to_load.txt", np.array(meta_failed_to_load), fmt="%s",header="record_name, file_name, error_message")
np.savetxt(metadata_output_dir / "ags_failed_to_load.txt", np.array(meta_ags_failed_to_load), fmt="%s",header="record_name, file_name, error_message")
np.savetxt(metadata_output_dir / "xls_failed_to_load.txt", np.array(meta_xls_failed_to_load), fmt="%s",header="record_name, file_name, error_message")
