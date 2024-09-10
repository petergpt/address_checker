import os
import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai_processor import OpenAIProcessor
from data_handler import DataHandler
from address_comparator import AddressComparator

def process_single_file(filename, processor, data_handler, comparator, ground_truth):
    """
    Process a single file: separate addresses, format them, and compare with ground truth.
    Returns a dictionary with the filename, pass/fail status, and any differences.
    """
    input_dir = 'input_data/'
    base_filename = os.path.splitext(filename)[0]
    step1_output_file = f'output_data/{base_filename}_step1.txt'
    step2_output_file = f'output_data/{base_filename}_step2.json'
    comparison_results_file = f'output_data/{base_filename}_comparison_results.json'

    print(f"Processing file: {filename}")

    input_file = os.path.join(input_dir, filename)

    # Step 1: Read the input CSV file
    input_addresses = data_handler.read_csv(input_file)
    if not input_addresses:
        print(f"Error: No addresses found in {filename}. Skipping file.")
        return {"filename": filename, "status": "FAILED", "reason": "No addresses found"}

    # Step 2: Separate the addresses (Step 1)
    separated_addresses = processor.separate_addresses(input_addresses, version="v1")
    if not separated_addresses:
        print(f"Error: Failed to separate addresses in {filename}.")
        return {"filename": filename, "status": "FAILED", "reason": "Address separation error"}

    data_handler.save_txt(step1_output_file, separated_addresses)

    # Step 3: Format the addresses (Step 2)
    formatted_addresses = processor.format_addresses(separated_addresses, version="v1")
    if not formatted_addresses:
        print(f"Error: Failed to format addresses in {filename}.")
        return {"filename": filename, "status": "FAILED", "reason": "Address formatting error"}

    data_handler.save_json(step2_output_file, formatted_addresses)

    # Step 4: Compare with the ground truth
    comparison_report = comparator.compare(formatted_addresses, ground_truth)
    data_handler.save_json(comparison_results_file, comparison_report)

    # Determine if test passed or failed
    if not comparison_report:
        return {"filename": filename, "status": "PASS"}
    else:
        return {"filename": filename, "status": "FAILED", "reason": f"{len(comparison_report)} differences found"}

def main():
    # Initialize components
    processor = OpenAIProcessor()
    data_handler = DataHandler()
    comparator = AddressComparator()

    # Directory for input files
    input_dir = 'input_data/'
    ground_truth_file = 'ground_truth.json'

    # Get the current time for the report file name
    now = datetime.datetime.now()
    report_file = now.strftime(f'output_data/test_report_%Y-%m-%d_%H-%M-%S.txt')

    # Get all CSV files from the input_data directory
    all_files = [f for f in os.listdir(input_dir) if f.endswith('.csv')]

    # Initialize report stats
    total_files = len(all_files)
    total_passes = 0
    total_failures = 0
    detailed_report = []

    # Step 1: Load the ground truth once
    print("Loading ground truth data...")
    ground_truth = data_handler.read_json(ground_truth_file)
    if not ground_truth:
        print(f"Error: Ground truth file {ground_truth_file} is missing or invalid.")
        return

    # Step 2: Get the prompts used
    separate_prompt = processor.get_prompt('separate_addresses', version="v1")
    format_prompt = processor.get_prompt('format_addresses', version="v1")

    # Step 3: Create the header for the report
    report_header = []
    report_header.append(f"Test Report - {now.strftime('%Y-%m-%d %H:%M:%S')}")
    report_header.append(f"Prompts Used:")
    report_header.append(f"Separate Addresses Prompt: {separate_prompt}")
    report_header.append(f"Format Addresses Prompt: {format_prompt}")
    report_header.append("="*80)
    report_header.append("")

    # Step 4: Process each file in parallel using ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=5) as executor:  # Adjust `max_workers` as needed
        futures = {executor.submit(process_single_file, filename, processor, data_handler, comparator, ground_truth): filename for filename in all_files}
        for future in as_completed(futures):
            result = future.result()
            if result['status'] == "PASS":
                total_passes += 1
                detailed_report.append(f"{result['filename']}: PASS")
            else:
                total_failures += 1
                detailed_report.append(f"{result['filename']}: FAILED - {result['reason']}")

    # Step 5: Write the detailed report
    report_footer = [
        "="*80,
        f"Total files tested: {total_files}",
        f"Total passes: {total_passes}",
        f"Total failures: {total_failures}",
        "="*80
    ]

    with open(report_file, 'w') as report:
        report.write("\n".join(report_header))
        report.write("\n".join(detailed_report))
        report.write("\n".join(report_footer))

    print(f"Test report saved to {report_file}")

if __name__ == "__main__":
    main()
