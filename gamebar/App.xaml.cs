using Microsoft.Gaming.XboxGameBar;
using Windows.ApplicationModel.Activation;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using Windows.Storage;
using System;

namespace RLHubGameBar
{
    sealed partial class App : Application
    {
        private XboxGameBarWidget widget;
        public App()
        {
            InitializeComponent();
            UnhandledException += async (sender, e) => {
                e.Handled = true;
                await SaveError("Unhandled", e.Exception);
            };
        }
        private async System.Threading.Tasks.Task SaveError(string stage, Exception error)
        {
            try {
                var file = await ApplicationData.Current.LocalFolder.CreateFileAsync("widget-startup.txt", CreationCollisionOption.ReplaceExisting);
                await FileIO.WriteTextAsync(file, stage + "\n" + error.ToString());
            } catch { }
        }
        protected override async void OnActivated(IActivatedEventArgs args)
        {
            string stage = "Protocol activation";
            try {
                XboxGameBarWidgetActivatedEventArgs activation = null;
                if (args.Kind == ActivationKind.Protocol) {
                    var protocol = args as IProtocolActivatedEventArgs;
                    if (protocol != null && protocol.Uri.Scheme == "ms-gamebarwidget")
                        activation = args as XboxGameBarWidgetActivatedEventArgs;
                }
                if (activation == null || !activation.IsLaunchActivation) return;
                var frame = new Frame();
                Window.Current.Content = frame;
                stage = "Game Bar connection";
                widget = new XboxGameBarWidget(activation, Window.Current.CoreWindow, frame);
                stage = "Overlay creation";
                // The page is authored in C#, so instantiate it directly instead
                // of asking the generated XAML metadata provider to activate it.
                frame.Content = new OverlayPage();
                Window.Current.Closed += (sender, e) => { widget = null; };
                stage = "Window activation";
                Window.Current.Activate();
            } catch (Exception error) {
                Window.Current.Content = new TextBlock {
                    Text = "RL Hub: " + stage + "\n" + error.Message,
                    TextWrapping = TextWrapping.Wrap, Margin = new Thickness(20)
                };
                Window.Current.Activate();
                await SaveError(stage, error);
            }
        }
        protected override void OnLaunched(LaunchActivatedEventArgs args)
        {
            Window.Current.Content = new TextBlock {
                Text = "Åpne Win + G, velg RL Hub og fest widgeten med tegnestiften. Velg Fullskjerm i RL Hubs Overlay-fane.",
                TextWrapping = TextWrapping.Wrap, Margin = new Thickness(30)
            };
            Window.Current.Activate();
        }
    }
}
