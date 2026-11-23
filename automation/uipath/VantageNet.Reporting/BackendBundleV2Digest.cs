#nullable enable
using System;
using System.Globalization;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;

namespace VantageNet.Reporting
{
    internal static class BackendBundleV2Digest
    {
        internal static string Sha256(byte[] bytes) => Convert.ToHexString(SHA256.HashData(bytes)).ToLowerInvariant();

        internal static string Reading(string fingerprint, JsonElement reading, JsonElement feedback)
        {
            var json = new StringBuilder("{\"feedback\":");
            Append(json, feedback);
            json.Append(",\"reading\":");
            Append(json, reading);
            json.Append(",\"submission_fingerprint\":");
            Quote(json, fingerprint);
            json.Append('}');
            return Sha256(new UTF8Encoding(false, true).GetBytes(json.ToString()));
        }

        private static void Append(StringBuilder json, JsonElement value)
        {
            switch (value.ValueKind)
            {
                case JsonValueKind.Object:
                    json.Append('{');
                    // The contract validates that every property name here is ASCII.
                    var fields = new System.Collections.Generic.SortedDictionary<string, JsonElement>(StringComparer.Ordinal);
                    foreach (var property in value.EnumerateObject()) fields.Add(property.Name, property.Value);
                    var first = true;
                    foreach (var property in fields)
                    {
                        if (!first) json.Append(',');
                        first = false;
                        Quote(json, property.Key);
                        json.Append(':');
                        Append(json, property.Value);
                    }
                    json.Append('}');
                    break;
                case JsonValueKind.Array:
                    json.Append('[');
                    var separator = "";
                    foreach (var entry in value.EnumerateArray())
                    {
                        json.Append(separator);
                        Append(json, entry);
                        separator = ",";
                    }
                    json.Append(']');
                    break;
                case JsonValueKind.String:
                    Quote(json, value.GetString()!);
                    break;
                case JsonValueKind.Number:
                    json.Append(Number(value));
                    break;
                default:
                    json.Append(value.GetRawText()); // true, false, null
                    break;
            }
        }

        private static void Quote(StringBuilder json, string value)
        {
            json.Append('"');
            foreach (var ch in value)
            {
                switch (ch)
                {
                    case '"': json.Append("\\\""); break;
                    case '\\': json.Append("\\\\"); break;
                    case '\b': json.Append("\\b"); break;
                    case '\f': json.Append("\\f"); break;
                    case '\n': json.Append("\\n"); break;
                    case '\r': json.Append("\\r"); break;
                    case '\t': json.Append("\\t"); break;
                    default:
                        if (ch < ' ') json.Append("\\u").Append(((int)ch).ToString("x4", CultureInfo.InvariantCulture));
                        else json.Append(ch);
                        break;
                }
            }
            json.Append('"');
        }

        private static string Number(JsonElement value)
        {
            var raw = value.GetRawText();
            if (!raw.Contains('.') && !raw.Contains('e') && !raw.Contains('E'))
                return raw == "-0" ? "0" : raw; // JSON integers have no extra leading zeros.

            var number = value.GetDouble();
            BackendBundleV2Contract.Require(double.IsFinite(number), "Non-finite number in reading digest payload.");
            var sign = BitConverter.DoubleToInt64Bits(number) < 0 ? "-" : "";
            if (number == 0) return sign + "0.0";

            // .NET round-trip format gives the shortest binary64 significand.
            // Apply CPython's fixed/scientific thresholds and exponent spelling.
            var parts = Math.Abs(number).ToString("R", CultureInfo.InvariantCulture).Split('E');
            var significand = parts[0];
            var decimalPoint = significand.IndexOf('.');
            var exponent = parts.Length == 2 ? int.Parse(parts[1], CultureInfo.InvariantCulture) : 0;
            exponent += (decimalPoint < 0 ? significand.Length : decimalPoint) - 1;
            var digits = significand.Replace(".", "");
            var significant = digits.TrimStart('0');
            exponent -= digits.Length - significant.Length;
            digits = significant.TrimEnd('0');

            if (exponent < -4 || exponent >= 16)
            {
                var mantissa = digits.Length == 1 ? digits : digits.Insert(1, ".");
                return sign + mantissa + (exponent < 0 ? "e-" : "e+")
                    + Math.Abs(exponent).ToString("D2", CultureInfo.InvariantCulture);
            }
            if (exponent < 0) return sign + "0." + new string('0', -exponent - 1) + digits;
            var position = exponent + 1;
            return sign + (digits.Length <= position ? digits.PadRight(position, '0') + ".0" : digits.Insert(position, "."));
        }
    }
}
