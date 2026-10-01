using System;
using System.Threading;
using System.Net.Http;
using Windows.Storage.Streams;
using Windows.UI.Xaml;
using Windows.UI.Xaml.Controls;
using Windows.UI.Xaml.Media;
using Windows.UI.Xaml.Media.Imaging;

namespace RLHubGameBar
{
    public sealed class OverlayPage : Page
    {
        private readonly Image card = new Image { Stretch = Stretch.Uniform, IsHitTestVisible = false };
        private readonly HttpClient client = new HttpClient { Timeout = TimeSpan.FromSeconds(1) };
        private readonly DispatcherTimer timer = new DispatcherTimer { Interval = TimeSpan.FromMilliseconds(500) };
        private readonly CancellationTokenSource stopping = new CancellationTokenSource();
        private bool updating;
        public OverlayPage()
        {
            Background = new SolidColorBrush(Windows.UI.Colors.Transparent);
            Content = card;
            IsHitTestVisible = false;
            timer.Tick += async (sender, args) => {
                if (updating) return;
                updating = true;
                try {
                    var bytes = await client.GetByteArrayAsync("http://127.0.0.1:18765/api/overlay/frame");
                    using (var stream = new InMemoryRandomAccessStream()) {
                        using (var writer = new DataWriter(stream.GetOutputStreamAt(0))) {
                            writer.WriteBytes(bytes);
                            await writer.StoreAsync();
                        }
                        stream.Seek(0);
                        var bitmap = new BitmapImage();
                        await bitmap.SetSourceAsync(stream);
                        if (!stopping.IsCancellationRequested) card.Source = bitmap;
                    }
                } catch { card.Source = null; }
                finally { updating = false; }
            };
            Loaded += (sender, args) => timer.Start();
            Unloaded += (sender, args) => { timer.Stop(); stopping.Cancel(); client.Dispose(); };
        }
    }
}
