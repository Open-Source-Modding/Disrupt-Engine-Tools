using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading.Tasks;

namespace Arada.External
{
    public class Havok
    {
        public static string ExtractHkrXml(FileInfo path, FileInfo destination)
        {
            ProcessStartInfo start = new ProcessStartInfo();
            start.FileName = @"external\havok\fileconvert\bin\windows\FileConvert.exe";
            start.Arguments = string.Format("{0} {1} {2}", path.FullName, destination.FullName, @"-x ");
            start.UseShellExecute = false;
            start.RedirectStandardOutput = true;
            using (Process process = Process.Start(start))
            {
                using (StreamReader reader = process.StandardOutput)
                {
                    string result = reader.ReadToEnd();
                    result = Regex.Replace(result, @"\t|\n|\r", "");
                    
                    return result;
                }
            }
        }
    }
}
