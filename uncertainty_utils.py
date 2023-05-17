import json
import os
import matplotlib.pyplot as plt
import pandas as pd
from IPython.display import display, Markdown, HTML
# from sklearn.isotonic import IsotonicRegression
import numpy as np

def read_jsonl(file_path):
    """
    Reads a JSON Lines file and returns a list of dictionaries.
    """
    data = []
    with open(file_path, "r") as file:
        for line in file:
            data.append(json.loads(line))
    return data

def strip_is_solved(results):
    """
    Strips the first character from the 'is_solved' field in each dictionary of the list 'results'.
    """
    for case in results:
        case['is_solved'] = case['is_solved'][1:]
        
    return results

def format_text(text):
    """
    Formats text for display in Jupyter Notebooks.
    """
    if isinstance(text, str):
        lines = text.split("\n")
    elif isinstance(text, list):
        lines = []
        for line in text:
            if isinstance(line, str):
                lines += line.split("\n")
            else:
                lines.append(str(line))
    else:
        raise ValueError("Unsupported text format. Expected string or list of strings.")
    
    formatted_lines = []
    for line in lines:
        if isinstance(line, str):
            leading_spaces = len(line) - len(line.lstrip(" "))
            formatted_line = "&nbsp;" * leading_spaces + line.lstrip(" ")
            formatted_lines.append(formatted_line)
        else:
            formatted_lines.append(str(line))
    
    formatted_text = "<br>".join(formatted_lines)
    return formatted_text

def display_results(results):
    """
    Displays the 'results' list of dictionaries in a formatted way in Jupyter Notebooks.
    """
    for i, result in enumerate(results):
        display(Markdown(f"### Result {i+1}"))
        for key, value in result.items():
            if isinstance(value, (str, list)):
                formatted_value = format_text(value)
                display(HTML(f"<b>{key.capitalize()}:</b><br>{formatted_value}"))
            else:
                display(Markdown(f"**{key.capitalize()}:** {value}"))
        display(Markdown("---"))

def convert_results_to_dataframe(results):
    """
    Converts the 'results' list of dictionaries to a Pandas DataFrame.
    """
    data = []
    for case in results:
        num_tests = len(case['internal_tests'])
        for i, (num_passing, is_solved) in enumerate(zip(case['num_internal_completion_passing'], case['is_solved'])):
            data.append({
                'Test Case': i+1,
                'Tests Passed': num_passing[0],
                'Total Tests': num_tests,
                'Response': is_solved
            })

    return pd.DataFrame(data)

def merge_points(grouped, tolerance=5):
    merged_data = []
    for group, data in grouped:
        total_tests = data['Total Tests'].iloc[0]
        percent_passed = group / total_tests * 100

        # Check if the point can be merged with an existing one
        for item in merged_data:
            if abs(item['percent_passed'] - percent_passed) <= tolerance:
                item['rows'].extend(data['Response'].tolist())
                break
        else:
            merged_data.append({
                'percent_passed': percent_passed,
                'rows': data['Response'].tolist()
            })

    return merged_data

def plot_results(ece, brier_score, df):
    """
    Plots the percentage of True rows for each percentage of tests passed using non-overlapping bars with error bars.
    """
    # Calculate percentage of True rows for each percent of tests passed and merge points within 5% of total tests passed
    grouped = df.groupby('Tests Passed')
    merged_data = merge_points(grouped)

    percent_passed = []
    percent_true = []
    num_rows = []
    for item in merged_data:
        percent_passed.append(item['percent_passed'])
        percent_true.append(sum(item['rows']) / len(item['rows']) * 100)
        num_rows.append(len(item['rows']))

    # Calculate the width and left edges of each bar based on the percentage range
    width = 5
    left_edges = [(p - width/2) for p in percent_passed]

    # Calculate the error bars
    error = [np.std(item['rows']) / len(item['rows']) * 100 for item in merged_data]
    
    # Create bar plot with error bars and the updated color
    plt.bar(left_edges, percent_true, width=width, align='edge', yerr=error, capsize=5)

    # Add axis labels
    plt.ylabel('Percent of Questions Answered Correctly')
    plt.xlabel('Percent of Internal Tests Passed')

    # Label each bar with the number of rows which contributed to that bar
    for i, txt in enumerate(num_rows):
        text_position = percent_true[i] + error[i] + 1
        if text_position > 100:  # Ensure text does not go beyond plot
            text_position = 100
        plt.annotate(txt, (left_edges[i], text_position), fontsize=8, xytext=(12, 4), textcoords='offset points', ha='right')

    # Add the line y=x
    min_value = min(min(percent_passed), min(percent_true))
    max_value = max(max(percent_passed), max(percent_true))
    plt.plot([min_value, max_value], [min_value, max_value], 'r--')
    
    # Create legend for the red dashed line
    plt.legend(['Perfect Calibration'], loc='upper left')

    # Add labels for expected calibration error and mean square error
    plt.text(0.05, 0.85, 'Expected Calibration\n Error: '+str(round(ece,2)), transform=plt.gca().transAxes, fontsize=10, va='top')
    plt.text(0.05, 0.7, 'Mean Square Error: '+str(round(brier_score,2)), transform=plt.gca().transAxes, fontsize=10, va='top')

    # print("before adjustment")
    # Show plot
    plt.show()

    
def calculate_calibration_error(df):
    """
    Calculates the expected calibration error for each percentage of tests passed.
    """
    # Calculate percentage of True rows for each percent of tests passed and merge points within 5% of total tests passed
    grouped = df.groupby('Tests Passed')
    merged_data = merge_points(grouped)

    percent_passed = []
    percent_true = []
    num_rows = []
    for item in merged_data:
        percent_passed.append(item['percent_passed'])
        percent_true.append(sum(item['rows']) / len(item['rows']) * 100)
        num_rows.append(len(item['rows']))

    # Calculate absolute differences between percent_passed and percent_true for each group
    abs_differences = [abs(p - t) for p, t in zip(percent_passed, percent_true)]

    # Calculate expected calibration error as a weighted average of abs_differences
    total_rows = sum(num_rows)
    calibration_error = sum(d * n for d, n in zip(abs_differences, num_rows)) / total_rows

    return calibration_error

def calculate_brier_score(df):
    """
    Calculates the Brier score for each prediction.
    """
    # Ensure the predictions and actual values are between 0 and 1
    df['Predicted Probability'] = (df['Tests Passed'] / df["Total Tests"])
    df['Actual Outcome'] = (df['Response'] == True) 

    # Calculate squared differences between the predicted probabilities and the actual outcomes
    df['Squared Differences'] = (df['Predicted Probability'] - df['Actual Outcome'])**2

    # Calculate the Brier score as the mean of the squared differences
    brier_score = df['Squared Differences'].mean()

    return brier_score
