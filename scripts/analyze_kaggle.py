import kagglehub
import csv
import os

path = kagglehub.dataset_download('shahriarkabir/procurement-kpi-analysis-dataset')
print('Downloaded to:', path)

for root, dirs, files in os.walk(path):
    for f in files:
        if f.endswith('.csv'):
            file_path = os.path.join(root, f)
            print('\nFile:', f)
            try:
                with open(file_path, 'r', encoding='utf-8') as f_in:
                    reader = csv.reader(f_in)
                    header = next(reader, None)
                    print('Columns:', header)
                    first_row = next(reader, None)
                    print('Row 1:', first_row)
            except Exception as e:
                print('Could not read:', e)
