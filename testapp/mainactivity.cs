using Android.App;
using Android.OS;
using Android.Widget;

namespace HelloWorldApp
{
    [Activity(Label = "HelloWorldApp", MainLauncher = true, Icon = "@drawable/icon", ScreenOrientation = Android.Content.PM.ScreenOrientation.Portrait)] // Bloque la rotation en mode portrait
    public class MainActivity : Activity
    {
        protected override void OnCreate(Bundle bundle)
        {
            base.OnCreate(bundle);
            // Définir le layout à partir de main.axml
            SetContentView(Resource.Layout.Main);

            // Afficher "Hello World"
            TextView textView = FindViewById<TextView>(Resource.Id.textView);
            textView.Text = "Hello World";
        }
    }
}