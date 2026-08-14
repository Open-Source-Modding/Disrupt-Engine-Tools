
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace Arada.classes
{
    public class ItemHavok
    {

        public void TestingHavok()
        {
            
            string path = Settings.settings.defaultDrive + @"arada\test\hkr\glmLogicTest_01_fabric.hkr";
            string path2 = Settings.settings.defaultDrive + @"arada\test\hkr\glmLogicTest_01_metal_hard.hkr";
            FileInfo fi = new FileInfo(path);
            FileInfo fi2 = new FileInfo(path2);
            string exportPath = Settings.settings.defaultTempDir + @"\" + fi.Name + ".xml";
            string exportPath2 = Settings.settings.defaultTempDir + @"\" + fi2.Name + ".xml";
            // var result = External.Havok.ExtractHkrXml(fi, new FileInfo(exportPath));
            // var result2 = External.Havok.ExtractHkrXml(fi2, new FileInfo(exportPath2));
            
            // hktagfile data = ReadXml.ReadXmlFile(exportPath, new hktagfile());

            // hktagfile


        }
    }
}
