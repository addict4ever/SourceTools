using Android.OS;
using Android.Views;
using Android.Widget;
using AndroidX.Fragment.App;
using SQLite;
using System.IO;
using Xamarin.Essentials;

namespace KnowledgeBaseApp
{
    public class AddEntryFragment : Fragment
    {
        EditText entryTitle, entryContent;
        Button addButton;
        string dbPath = Path.Combine(FileSystem.AppDataDirectory, "knowledge.db");

        public override View OnCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState)
        {
            View view = inflater.Inflate(Resource.Layout.fragment_add, container, false);
            entryTitle = view.FindViewById<EditText>(Resource.Id.entryTitle);
            entryContent = view.FindViewById<EditText>(Resource.Id.entryContent);
            addButton = view.FindViewById<Button>(Resource.Id.addButton);

            addButton.Click += AddEntry;
            return view;
        }

        void AddEntry(object sender, System.EventArgs e)
        {
            var db = new SQLiteConnection(dbPath);
            db.CreateTable<KnowledgeEntry>();

            var newEntry = new KnowledgeEntry
            {
                Title = entryTitle.Text,
                Content = entryContent.Text
            };
            db.Insert(newEntry);
            Toast.MakeText(Activity, "Entry added", ToastLength.Short).Show();
        }
    }
}