using System.Text;
using System.Text.RegularExpressions;

namespace WorkshopTracker.App.Services;

public static partial class TextNormalizer
{
    public static string Normalize(string? value)
    {
        if (string.IsNullOrWhiteSpace(value)) return string.Empty;
        var text = value.Trim().ToUpperInvariant()
            .Replace('\u2014', '-').Replace('\u2013', '-')
            .Replace('(', ' ').Replace(')', ' ')
            .Replace('[', ' ').Replace(']', ' ');
        text = Whitespace().Replace(text, " ");
        return text.Trim();
    }

    public static string StableKey(string? serial, string? workOrder, string? designation, string? name, string? contract)
    {
        var parts = new[] { serial, workOrder, designation, name, contract }
            .Select(Normalize).Where(p => p.Length > 0);
        return string.Join('|', parts);
    }

    [GeneratedRegex(@"\s+")]
    private static partial Regex Whitespace();
}
