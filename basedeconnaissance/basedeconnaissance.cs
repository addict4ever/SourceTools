using Android.App;
using Android.OS;
using Android.Widget;
using AndroidX.AppCompat.App;
using System;
using System.IO;
using SQLite;
using Xamarin.Essentials;

namespace KnowledgeBaseApp
{
    [Activity(Label = "Knowledge Base", MainLauncher = true)]
    public class MainActivity : AppCompatActivity
    {
        EditText entryTitle, entryContent;
        Button addButton, searchButton;
        TextView resultText;
        string dbPath = Path.Combine(FileSystem.AppDataDirectory, "knowledge.db");

        protected override void OnCreate(Bundle savedInstanceState)
        {
            base.OnCreate(savedInstanceState);
            SetContentView(Resource.Layout.activity_main);

            entryTitle = FindViewById<EditText>(Resource.Id.entryTitle);
            entryContent = FindViewById<EditText>(Resource.Id.entryContent);
            addButton = FindViewById<Button>(Resource.Id.addButton);
            searchButton = FindViewById<Button>(Resource.Id.searchButton);
            resultText = FindViewById<TextView>(Resource.Id.resultText);

            CreateDatabase();

            addButton.Click += AddEntry;
            searchButton.Click += SearchEntry;
        }

        void CreateDatabase()
        {
            var db = new SQLiteConnection(dbPath);
            db.CreateTable<KnowledgeEntry>();
        }

        void AddEntry(object sender, EventArgs e)
        {
            var db = new SQLiteConnection(dbPath);
            var newEntry = new KnowledgeEntry
            {
                Title = entryTitle.Text,
                Content = entryContent.Text
            };
            db.Insert(newEntry);
            Toast.MakeText(this, "Entry added", ToastLength.Short).Show();
        }

        void SearchEntry(object sender, EventArgs e)
        {
            var db = new SQLiteConnection(dbPath);
            var result = db.Table<KnowledgeEntry>().FirstOrDefault(e => e.Title.Contains(entryTitle.Text));
            if (result != null)
            {
                resultText.Text = $"Title: {result.Title}\nContent: {result.Content}";
            }
            else
            {
                resultText.Text = "No entry found";
            }
        }
    }

    public class KnowledgeEntry
    {
        [PrimaryKey, AutoIncrement]
        public int Id { get; set; }
        public string Title { get; set; }
        public string Content { get; set; }  // Can store links, text, paths to files
    }
}