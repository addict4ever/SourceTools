using Android.OS;
using Android.Views;
using Android.Widget;
using AndroidX.Fragment.App;
using SQLite;
using System.IO;
using Xamarin.Essentials;
using Newtonsoft.Json;
using CsvHelper;
using System.Globalization;
using System.Collections.Generic;
using System.Linq;

namespace KnowledgeBaseApp
{
    public class ImportFragment : Fragment
    {
        Button importJsonButton, importCsvButton;
        string dbPath = Path.Combine(FileSystem.AppDataDirectory, "knowledge.db");

        public override View OnCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState)
        {
            View view = inflater.Inflate(Resource.Layout.fragment_import, container, false);
            importJsonButton = view.FindViewById<Button>(Resource.Id.importJsonButton);
            importCsvButton = view.FindViewById<Button>(Resource.Id.importCsvButton);

            importJsonButton.Click += ImportJson;
            importCsvButton.Click += ImportCsv;
            return view;
        }

        async void ImportJson(object sender, System.EventArgs e)
        {
            var fileResult = await FilePicker.PickAsync();
            if (fileResult != null)
            {
                string jsonContent = await File.ReadAllTextAsync(fileResult.FullPath);
                var entries = JsonConvert.DeserializeObject<List<KnowledgeEntry>>(jsonContent);

                var db = new SQLiteConnection(dbPath);
                db.CreateTable<KnowledgeEntry>();

                foreach (var entry in entries)
                {
                    db.Insert(entry);
                }

                Toast.MakeText(Activity, "JSON imported successfully", ToastLength.Short).Show();
            }
        }

        async void ImportCsv(object sender, System.EventArgs e)
        {
            var fileResult = await FilePicker.PickAsync();
            if (fileResult != null)
            {
                using (var reader = new StreamReader(fileResult.FullPath))
                using (var csv = new CsvReader(reader, CultureInfo.InvariantCulture))
                {
                    var entries = csv.GetRecords<KnowledgeEntry>().ToList();

                    var db = new SQLiteConnection(dbPath);
                    db.CreateTable<KnowledgeEntry>();

                    foreach (var entry in entries)
                    {
                        db.Insert(entry);
                    }

                    Toast.MakeText(Activity, "CSV imported successfully", ToastLength.Short).Show();
                }
            }
        }
    }

    public class KnowledgeEntry
    {
        [PrimaryKey, AutoIncrement]
        public int Id { get; set; }
        public string Title { get; set; }
        public string Content { get; set; }
        public string Metadata { get; set; }  // Meta-data field for storing tags or other info
    }
}