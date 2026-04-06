using Microsoft.UI.Xaml;
using Microsoft.UI.Xaml.Controls;

namespace AlexaSettingsWinUI.Controls;

/// <summary>WrapPanel — WinUI 3 не має вбудованого.</summary>
public class WrapPanel : Panel
{
    public double ItemSpacing { get; set; } = 8;
    public double LineSpacing { get; set; } = 8;

    protected override Windows.Foundation.Size MeasureOverride(Windows.Foundation.Size available)
    {
        double x = 0, y = 0, rowH = 0;
        foreach (UIElement child in Children)
        {
            child.Measure(available);
            var s = child.DesiredSize;
            if (x > 0 && x + s.Width > available.Width) { y += rowH + LineSpacing; rowH = 0; x = 0; }
            x += s.Width + ItemSpacing;
            rowH = Math.Max(rowH, s.Height);
        }
        return new Windows.Foundation.Size(available.Width, y + rowH);
    }

    protected override Windows.Foundation.Size ArrangeOverride(Windows.Foundation.Size final)
    {
        double x = 0, y = 0, rowH = 0;
        foreach (UIElement child in Children)
        {
            var s = child.DesiredSize;
            if (x > 0 && x + s.Width > final.Width) { y += rowH + LineSpacing; rowH = 0; x = 0; }
            child.Arrange(new Windows.Foundation.Rect(x, y, s.Width, s.Height));
            x += s.Width + ItemSpacing;
            rowH = Math.Max(rowH, s.Height);
        }
        return final;
    }
}
