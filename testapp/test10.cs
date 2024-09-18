using Android.App;
using Android.OS;
using Android.Widget;
using Android.Content.PM;
using Android.Telephony;
using Android.Content;
using Android.Provider;
using Android.Net;
using AndroidX.Core.App;
using AndroidX.Core.Content;
using Android;
using Android.Net.Wifi;
using System;
using System.Collections.Generic;
using System.Linq;

namespace AndroidApp1
{
    [Activity(Label = "DeviceInfoApp", MainLauncher = true)]
    public class MainActivity : Activity
    {
        protected override void OnCreate(Bundle bundle)
        {
            base.OnCreate(bundle);
            SetContentView(Resource.Layout.activity_main);

            // Ajout d'un Toast pour signaler le démarrage de l'activité
            Toast.MakeText(this, "Activité démarrée", ToastLength.Short).Show();

            // Vérifiez et demandez les autorisations nécessaires
            CheckPermissions();

            try
            {
                // Récupérer et afficher les informations de l'appareil
                string deviceInfo = GetDeviceInfo();
                string storageInfo = GetAvailableStorage();
                string memoryInfo = GetMemoryInfo();
                string simInfo = GetSimInfo();
                string ipInfo = GetIpAddress();

                // Obtenir les contacts, SMS et appels
                var contacts = GetContacts();
                var sms = GetSms();
                var callLogs = GetCallLog();

                // Affichage des informations dans un TextView
                var textView = FindViewById<TextView>(Resource.Id.textView);
                textView.Text = $"Infos Appareil: {deviceInfo}\n\n" +
                                $"Espace Disque: {storageInfo}\n\n" +
                                $"RAM: {memoryInfo}\n\n" +
                                $"Infos SIM: {simInfo}\n\n" +
                                $"IP: {ipInfo}\n\n" +
                                $"Contacts: {string.Join("\n", contacts)}\n\n" +
                                $"SMS: {string.Join("\n", sms)}\n\n" +
                                $"Appels: {string.Join("\n", callLogs)}";

                // Afficher un Toast pour indiquer que les informations ont été récupérées avec succès
                Toast.MakeText(this, "Informations collectées avec succès", ToastLength.Long).Show();
            }
            catch (Exception ex)
            {
                // Afficher un Toast en cas d'erreur
                Toast.MakeText(this, $"Erreur: {ex.Message}", ToastLength.Long).Show();
            }
        }

        // Vérification et demande des permissions
        private void CheckPermissions()
        {
            List<string> permissionsNeeded = new List<string>();

            if (ContextCompat.CheckSelfPermission(this, Manifest.Permission.ReadContacts) != (int)Permission.Granted)
                permissionsNeeded.Add(Manifest.Permission.ReadContacts);

            if (ContextCompat.CheckSelfPermission(this, Manifest.Permission.ReadSms) != (int)Permission.Granted)
                permissionsNeeded.Add(Manifest.Permission.ReadSms);

            if (ContextCompat.CheckSelfPermission(this, Manifest.Permission.ReadCallLog) != (int)Permission.Granted)
                permissionsNeeded.Add(Manifest.Permission.ReadCallLog);

            if (permissionsNeeded.Count > 0)
            {
                ActivityCompat.RequestPermissions(this, permissionsNeeded.ToArray(), 1);
            }
        }

        // Obtenir les informations générales sur l'appareil
        public string GetDeviceInfo()
        {
            Toast.MakeText(this, "Récupération des infos appareil", ToastLength.Short).Show();

            string manufacturer = Android.OS.Build.Manufacturer;
            string model = Android.OS.Build.Model;
            string version = Android.OS.Build.VERSION.Release;
            string deviceName = Android.OS.Build.Device;

            return $"Fabricant: {manufacturer}, Modèle: {model}, Version: {version}, Nom de l'appareil: {deviceName}";
        }

        // Obtenir l'espace de stockage disponible
        public string GetAvailableStorage()
        {
            try
            {
                StatFs stat = new StatFs(Android.OS.Environment.ExternalStorageDirectory.Path);
                long bytesAvailable = stat.BlockSizeLong * stat.AvailableBlocksLong;
                return FormatSize(bytesAvailable);
            }
            catch (Exception ex)
            {
                Toast.MakeText(this, $"Erreur lors de la récupération du stockage: {ex.Message}", ToastLength.Long).Show();
                return "Erreur lors de la récupération du stockage.";
            }
        }

        // Formater la taille des données en Ko, Mo, Go
        public string FormatSize(long size)
        {
            string suffix = null;
            double readableSize = size;
            if (readableSize >= 1024)
            {
                suffix = "Ko";
                readableSize /= 1024;
                if (readableSize >= 1024)
                {
                    suffix = "Mo";
                    readableSize /= 1024;
                    if (readableSize >= 1024)
                    {
                        suffix = "Go";
                        readableSize /= 1024;
                    }
                }
            }
            return $"{readableSize:F2} {suffix}";
        }

        // Obtenir les informations sur la mémoire RAM
        public string GetMemoryInfo()
        {
            try
            {
                ActivityManager activityManager = (ActivityManager)GetSystemService(Context.ActivityService);
                ActivityManager.MemoryInfo memoryInfo = new ActivityManager.MemoryInfo();
                activityManager.GetMemoryInfo(memoryInfo);
                double availMemGB = memoryInfo.AvailMem / (1024.0 * 1024 * 1024);
                double totalMemGB = memoryInfo.TotalMem / (1024.0 * 1024 * 1024);
                return $"RAM Disponible: {availMemGB:F2} Go / {totalMemGB:F2} Go";
            }
            catch (Exception ex)
            {
                Toast.MakeText(this, $"Erreur lors de la récupération de la RAM: {ex.Message}", ToastLength.Long).Show();
                return "Erreur lors de la récupération de la RAM.";
            }
        }

        // Obtenir les informations sur la carte SIM
        public string GetSimInfo()
        {
            try
            {
                TelephonyManager telephonyManager = (TelephonyManager)GetSystemService(Context.TelephonyService);
                string phoneNumber = telephonyManager.Line1Number ?? "Non disponible";
                string operatorName = telephonyManager.NetworkOperatorName ?? "Non disponible";
                return $"Numéro de téléphone: {phoneNumber}\nOpérateur: {operatorName}";
            }
            catch (Exception ex)
            {
                Toast.MakeText(this, $"Erreur lors de la récupération des infos SIM: {ex.Message}", ToastLength.Long).Show();
                return "Erreur lors de la récupération des infos SIM.";
            }
        }

        // Obtenir les contacts
        public List<string> GetContacts()
        {
            List<string> contacts = new List<string>();
            try
            {
                var uri = ContactsContract.CommonDataKinds.Phone.ContentUri;
                string[] projection = { ContactsContract.Contacts.InterfaceConsts.DisplayName, ContactsContract.CommonDataKinds.Phone.Number };
                var cursor = ContentResolver.Query(uri, projection, null, null, null);

                if (cursor != null && cursor.MoveToFirst())
                {
                    int nameIndex = cursor.GetColumnIndex(projection[0]);
                    int numberIndex = cursor.GetColumnIndex(projection[1]);

                    do
                    {
                        string name = cursor.GetString(nameIndex);
                        string number = cursor.GetString(numberIndex);
                        contacts.Add($"{name}: {number}");
                    } while (cursor.MoveToNext());

                    cursor.Close();
                }
                else
                {
                    Toast.MakeText(this, "Aucun contact trouvé.", ToastLength.Short).Show();
                }
            }
            catch (Exception ex)
            {
                Toast.MakeText(this, $"Erreur lors de la récupération des contacts: {ex.Message}", ToastLength.Long).Show();
            }
            return contacts;
        }

        // Obtenir les SMS
        public List<string> GetSms()
        {
            List<string> smsList = new List<string>();
            try
            {
                var uriSms = Android.Net.Uri.Parse("content://sms/inbox");
                var cursor = ContentResolver.Query(uriSms, null, null, null, null);

                if (cursor != null && cursor.MoveToFirst())
                {
                    int bodyIndex = cursor.GetColumnIndex("body");

                    do
                    {
                        string smsBody = cursor.GetString(bodyIndex);
                        smsList.Add(smsBody);
                    } while (cursor.MoveToNext());

                    cursor.Close();
                }
                else
                {
                    Toast.MakeText(this, "Aucun SMS trouvé.", ToastLength.Short).Show();
                }
            }
            catch (Exception ex)
            {
                Toast.MakeText(this, $"Erreur lors de la récupération des SMS: {ex.Message}", ToastLength.Long).Show();
            }
            return smsList;
        }

        // Obtenir les journaux d'appels
        public List<string> GetCallLog()
        {
            List<string> callLogs = new List<string>();
            try
            {
                var uri = CallLog.Calls.ContentUri;
                string[] projection = { CallLog.Calls.Number, CallLog.Calls.Type, CallLog.Calls.Date, CallLog.Calls.Duration };
                var cursor = ContentResolver.Query(uri, projection, null, null, null);

                if (cursor != null && cursor.MoveToFirst())
                {
                    int numberIndex = cursor.GetColumnIndex(projection[0]);
                    int typeIndex = cursor.GetColumnIndex(projection[1]);
                    int dateIndex = cursor.GetColumnIndex(projection[2]);
                    int durationIndex = cursor.GetColumnIndex(projection[3]);

                    do
                    {
                        string number = cursor.GetString(numberIndex);
                        string type = GetCallType(cursor.GetInt(typeIndex));
                        string date = new DateTime(1970, 1, 1).AddMilliseconds(cursor.GetLong(dateIndex)).ToString();
                        string duration = cursor.GetString(durationIndex);
                        callLogs.Add($"Numéro: {number}, Type: {type}, Date: {date}, Durée: {duration} sec");
                    } while (cursor.MoveToNext());

                    cursor.Close();
                }
                else
                {
                    Toast.MakeText(this, "Aucun journal d'appels trouvé.", ToastLength.Short).Show();
                }
            }
            catch (Exception ex)
            {
                Toast.MakeText(this, $"Erreur lors de la récupération des journaux d'appels: {ex.Message}", ToastLength.Long).Show();
            }
            return callLogs;
        }

        // Convertir le type d'appel en texte lisible
        private string GetCallType(int type)
        {
            switch (type)
            {
                case (int)CallType.Incoming:
                    return "Appel entrant";
                case (int)CallType.Outgoing:
                    return "Appel sortant";
                case (int)CallType.Missed:
                    return "Appel manqué";
                default:
                    return "Inconnu";
            }
        }

        // Obtenir l'adresse IP
        public string GetIpAddress()
        {
            try
            {
                WifiManager wifiManager = (WifiManager)GetSystemService(WifiService);
                int ipAddressInt = wifiManager.ConnectionInfo.IpAddress;
                var ipAddressBytes = BitConverter.GetBytes(ipAddressInt);

                if (BitConverter.IsLittleEndian)
                {
                    Array.Reverse(ipAddressBytes);
                }

                var ipAddress = new System.Net.IPAddress(ipAddressBytes);
                return ipAddress.ToString();
            }
            catch (Exception ex)
            {
                Toast.MakeText(this, $"Erreur lors de la récupération de l'adresse IP: {ex.Message}", ToastLength.Long).Show();
                return "Erreur lors de la récupération de l'adresse IP.";
            }
        }
    }
}