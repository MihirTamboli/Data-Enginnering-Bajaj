import pandas as pd
import re

def find_absence_streaks(attendance_df):
    # Sort data by student_id and attendance_date
    attendance_df = attendance_df.sort_values(by=['student_id', 'attendance_date'])

    # Convert attendance_date to datetime
    attendance_df['attendance_date'] = pd.to_datetime(attendance_df['attendance_date'])

    # Create a new column to identify streaks
    attendance_df['prev_day'] = attendance_df.groupby('student_id')['attendance_date'].shift(1)
    attendance_df['day_diff'] = (attendance_df['attendance_date'] - attendance_df['prev_day']).dt.days

    # Identify streaks: break a streak if the day difference is not 1 or if the status is 'Present'
    attendance_df['streak'] = (attendance_df['day_diff'] != 1) | (attendance_df['status'] == 'Present')

    # Group by streaks to find start and end of absences
    streaks = attendance_df.groupby(['student_id', attendance_df['streak'].cumsum()])

    absences = []
    for _, group in streaks:
        # If all the days in the group are marked as 'Absent' and it's 3 or more days, record as a streak
        if group['status'].eq('Absent').all() and len(group) >= 3:
            absences.append({
                'student_id': group['student_id'].iloc[0],
                'absence_start_date': group['attendance_date'].min(),
                'absence_end_date': group['attendance_date'].max(),
                'total_absent_days': len(group)
            })

    return pd.DataFrame(absences)

def validate_email(email):
    # Email validation regex
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*@[a-zA-Z0-9]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def join_and_validate_students(absence_df, students_df):
    # Merge absence streaks with students data
    merged_df = pd.merge(absence_df, students_df, on='student_id', how='left')

    # Validate emails
    merged_df['email'] = merged_df['parent_email'].apply(lambda email: email if validate_email(email) else None)

    # Add msg column for valid emails
    merged_df['msg'] = merged_df.apply(
        lambda row: f"Dear Parent, your child {row['student_name']} was absent from {row['absence_start_date']} to {row['absence_end_date']} for {row['total_absent_days']} days. Please ensure their attendance improves."
        if row['email'] else None, axis=1
    )

    return merged_df[['student_id', 'absence_start_date', 'absence_end_date', 'total_absent_days', 'email', 'msg']]

def run(attendance_df, students_df):
    # Step 1: Find absence streaks
    absence_df = find_absence_streaks(attendance_df)
    
    # Step 2: Join with student data and validate emails
    final_df = join_and_validate_students(absence_df, students_df)
    
    # Return the final dataframe with required columns
    return final_df

# Load your datasets (replace with actual file paths)
attendance_df = pd.read_excel('data.xlsx')  # Replace with your actual file path
students_df = pd.read_excel('data.xlsx')  # Replace with your actual file path

# Run the process with the dataset
result_df = run(attendance_df, students_df)

# Show the result
print(result_df)
