import json
from fuzzywuzzy import fuzz

class AddressComparator:

    def compare(self, processed_addresses, ground_truth, match_threshold=60, compare_threshold=70):
        """
        Step 1: Fuzzy match the processed addresses to the ground truth using weighted matching.
        Step 2: Precisely compare the fields of the matched addresses.

        match_threshold: The threshold for fuzzy matching (default is 60%).
        compare_threshold: The threshold for precise field comparison (default is 70% for partial matching).
        """
        comparison_report = []
        successful_matches = 0
        unmatched_entries = 0

        # Helper function for fuzzy matching
        def is_fuzzy_match(str1, str2, threshold):
            """
            Uses fuzzy string matching to determine if two strings are close enough.
            Returns True if the similarity score is above the given threshold.
            """
            return fuzz.ratio(str1.lower(), str2.lower()) >= threshold

        # Helper function to normalize postcodes (remove spaces)
        def normalize_postcode(postcode):
            return postcode.replace(" ", "").lower() if postcode else ""

        # Helper function to find the best match from the ground truth with weighted scoring
        def find_best_match(processed_addr, ground_truth):
            """
            Compare processed_addr with each entry in the ground truth and return the best match using weighted scoring.
            Postcodes are weighted heavily, while names and streets have lower weights.
            """
            best_match = None
            best_score = 0
            best_truth_index = None

            for idx, truth_addr in enumerate(ground_truth):
                first_name_score = fuzz.ratio(processed_addr['FirstName'].lower(), truth_addr['FirstName'].lower())
                last_name_score = fuzz.ratio(processed_addr['LastName'].lower(), truth_addr['LastName'].lower())
                street_score = fuzz.ratio(processed_addr['StreetName'].lower(), truth_addr['StreetName'].lower())
                town_score = fuzz.ratio(processed_addr['Town'].lower(), truth_addr['Town'].lower())
                postcode_score = fuzz.ratio(normalize_postcode(processed_addr['Postcode']), normalize_postcode(truth_addr['Postcode']))

                # Apply weighted scoring to favor postcode matches
                total_score = (postcode_score * 3 + last_name_score * 2 + first_name_score + street_score + town_score) / 8

                # Only consider matches where postcodes are reasonably similar
                if postcode_score > match_threshold and total_score > best_score:
                    best_score = total_score
                    best_match = truth_addr
                    best_truth_index = idx

            return best_match, best_score, best_truth_index

        # Step 1: Fuzzy match records and find the best match for each processed address
        matches = []  # Store pairs of matched records
        matched_ground_truth_indices = set()  # Keep track of which ground truth records have been matched

        for processed_addr in processed_addresses:
            best_match, best_score, best_truth_index = find_best_match(processed_addr, ground_truth)

            # Only match if we have a strong enough match based on the weighted score
            if best_match and best_truth_index not in matched_ground_truth_indices and best_score >= match_threshold:
                matches.append((processed_addr, best_match, best_truth_index, best_score))
                matched_ground_truth_indices.add(best_truth_index)
            else:
                # If no match is found, mark the processed address as unmatched
                comparison_report.append({
                    "processed_address": processed_addr,
                    "ground_truth": None,
                    "differences": [{"field": "Missing entry", "processed_value": processed_addr, "expected_value": None}]
                })
                unmatched_entries += 1

        # Step 2: Precisely compare the matched records
        for processed, truth, truth_index, match_score in matches:
            differences = []

            # Compare important fields with precise matching
            if not is_fuzzy_match(processed['FirstName'], truth['FirstName'], compare_threshold):
                differences.append({
                    "field": "FirstName",
                    "processed_value": processed['FirstName'],
                    "expected_value": truth['FirstName']
                })

            if not is_fuzzy_match(processed['LastName'], truth['LastName'], compare_threshold):
                differences.append({
                    "field": "LastName",
                    "processed_value": processed['LastName'],
                    "expected_value": truth['LastName']
                })

            if not is_fuzzy_match(processed['StreetName'], truth['StreetName'], compare_threshold):
                differences.append({
                    "field": "StreetName",
                    "processed_value": processed['StreetName'],
                    "expected_value": truth['StreetName']
                })

            if not is_fuzzy_match(processed['Town'], truth['Town'], compare_threshold):
                differences.append({
                    "field": "Town",
                    "processed_value": processed['Town'],
                    "expected_value": truth['Town']
                })

            if normalize_postcode(processed['Postcode']) != normalize_postcode(truth['Postcode']):
                differences.append({
                    "field": "Postcode",
                    "processed_value": processed['Postcode'],
                    "expected_value": truth['Postcode']
                })

            if processed['Country'].lower() != truth['Country'].lower():
                differences.append({
                    "field": "Country",
                    "processed_value": processed['Country'],
                    "expected_value": truth['Country']
                })

            # Log the differences or successful match
            if differences:
                comparison_report.append({
                    "processed_address": processed,
                    "ground_truth": truth,
                    "differences": differences,
                    "match_score": match_score
                })
            else:
                successful_matches += 1  # Count successful matches

        # Handle unmatched ground truth records
        for idx, truth_addr in enumerate(ground_truth):
            if idx not in matched_ground_truth_indices:
                comparison_report.append({
                    "processed_address": None,
                    "ground_truth": truth_addr,
                    "differences": [{"field": "Missing entry", "processed_value": None, "expected_value": truth_addr}]
                })
                unmatched_entries += 1

        # Log match and mismatch counts
        print(f"Matched addresses: {successful_matches}")
        print(f"Unmatched or differing addresses: {unmatched_entries + len(comparison_report)}")

        # Return comparison report
        return comparison_report
