using Android.OS;
using Android.Views;
using Android.Widget;
using AndroidX.Fragment.App;
using SQLite;
using System.IO;
using Xamarin.Essentials;

namespace KnowledgeBaseApp
{
    public class SearchFragment : Fragment
    {
        EditText searchQuery;
        Button searchButton;
        TextView searchResult;
        string dbPath = Path.Combine(FileSystem.AppDataDirectory, "knowledge.db");

        public override View OnCreateView(LayoutInflater inflater, ViewGroup container, Bundle savedInstanceState)
        {
            View view = inflater.Inflate(Resource.Layout.fragment_search, container, false);
            searchQuery = view.FindViewById<EditText>(Resource.Id.searchQuery);
            searchButton = view.FindViewById<Button>(Resource.Id.searchButton);
            searchResult = view.FindViewById<TextView>(Resource.Id.searchResult);

            searchButton.Click += SearchEntry;
            return view;
        }

        void SearchEntry(object sender, System.EventArgs e)
        {
            var db = new SQLiteConnection(dbPath);
            var result = db.Table<KnowledgeEntry>()
                .FirstOrDefault(e => e.Title.Contains(searchQuery.Text) || e.Content.Contains(searchQuery.Text));

            if (result != null)
            {
                searchResult.Text = $"Title: {result.Title}\nContent: {result.Content}";
            }
            else
            {
                searchResult.Text = "No entry found";
            }
        }
    }
}