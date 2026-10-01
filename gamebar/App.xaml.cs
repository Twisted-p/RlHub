using Microsoft.Gaming.XboxGameBar;
using Windows.ApplicationModel.Activation;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;

namespace RLHubGameBar
{
    sealed partial class App : Application
    {
        private XboxGameBarWidget widget;
        public App() { InitializeComponent(); }
        protected override void OnActivated(IActivatedEventArgs args)
        {
            var activation = args as XboxGameBarWidgetActivatedEventArgs;
            if (activation == null || !activation.IsLaunchActivation) return;
            var frame = new Frame();
            Window.Current.Content = frame;
            widget = new XboxGameBarWidget(activation, Window.Current.CoreWindow, frame);
            frame.Navigate(typeof(OverlayPage));
            Window.Current.Closed += (sender, e) => { widget = null; };
            Window.Current.Activate();
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
