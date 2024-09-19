using Android.App;
using Android.OS;
using Android.Webkit;
using Android.Views;
using Android.Widget;
using Xamarin.Essentials;

namespace WebViewApp
{
    [Activity(Label = "WebViewApp", MainLauncher = true, Theme = "@android:style/Theme.NoTitleBar.Fullscreen", ConfigurationChanges = Android.Content.PM.ConfigChanges.Orientation | Android.Content.PM.ConfigChanges.ScreenSize)]
    public class MainActivity : Activity
    {
        WebView webView;

        protected override void OnCreate(Bundle savedInstanceState)
        {
            base.OnCreate(savedInstanceState);
            // Set view to the activity_main layout
            SetContentView(Resource.Layout.activity_main);

            webView = FindViewById<WebView>(Resource.Id.webView);
            webView.Settings.JavaScriptEnabled = true;

            // Enable zoom controls
            webView.Settings.BuiltInZoomControls = true;
            webView.Settings.DisplayZoomControls = false;

            // WebView client to handle loading pages and error handling
            webView.SetWebViewClient(new WebViewClient()
            {
                OnReceivedError = (view, request, error) =>
                {
                    Toast.MakeText(this, "Connection error. Please check your internet.", ToastLength.Long).Show();
                    webView.LoadUrl("about:blank");
                }
            });

            // Load the URL
            webView.LoadUrl("https://www.her.ma");
        }

        public override void OnBackPressed()
        {
            // Check if the WebView can go back
            if (webView.CanGoBack())
            {
                webView.GoBack();
            }
            else
            {
                base.OnBackPressed();
            }
        }
    }
}