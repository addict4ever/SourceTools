import metakit
import pandas as pd

# Specify your input and output files
input_file = "your_database.mk4"
output_file = "output.xlsx"

# Open the Metakit .mk4 file
db = metakit.storage(input_file, 0)

# List all views (tables) in the .mk4 file
views = db.getallviews()
print(f"Found views: {views}")

# Initialize a writer for Excel
with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
    # Iterate through each view in the database
    for view_name in views:
        view = db.view(view_name)
        data = []

        # Extract all records from the view
        for record in view:
            # Convert record to a dictionary
            record_dict = {field: record[field] for field in record.keys()}
            data.append(record_dict)

        # Create a DataFrame from the data
        if data:
            df = pd.DataFrame(data)
            # Save the DataFrame to a sheet in the Excel file
            df.to_excel(writer, sheet_name=view_name, index=False)

# Close the Metakit database
db.commit()
db.close()

print(f"Data has been successfully exported to {output_file}")