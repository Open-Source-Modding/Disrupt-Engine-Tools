using System;
using System.Collections.Generic;
using System.IO;
using System.Xml;
using System.Diagnostics;

namespace AnimationReport
{
    class Program
    {
        static string datapath;

        public static List<String> animations;
        static List<String> blendtrees;

        public static void GetAnimationsFromBlendtrees()
        {
            DirectoryInfo di_blendtrees = new DirectoryInfo(datapath  + @"\move\blendtrees");

            if (di_blendtrees.Exists)
            {
                FileInfo[] fi_blendtrees = di_blendtrees.GetFiles("*.move.xml", SearchOption.AllDirectories);
                foreach (FileInfo fi in fi_blendtrees)
                {
                    XmlDocument doc = new XmlDocument();
                    doc.Load(fi.FullName);
                    XmlNodeList animparams = doc.SelectNodes(".//AnimParam");
                    foreach (XmlNode n in animparams)
                    {
                        if (n.Attributes["AnimID"] != null)
                        {
                            String szAnimName = n.Attributes["AnimID"].Value.ToLower();
                            if (!animations.Contains(szAnimName))
                            {
                                animations.Add(szAnimName);
                            }
                        }
                    }
                }
            }
            else
            {
                Console.WriteLine("Cannot find the specified file directory");
            }
            Console.Write("\nPress any key to continue... ");
            Console.ReadLine();
        }

        static void GetBlendtreesFromDecisionTrees(string path)
        {
            DirectoryInfo di_decisiontrees = new DirectoryInfo(path);

            if (di_decisiontrees.Exists)
            {
                FileInfo[] fi_decisiontrees = di_decisiontrees.GetFiles("*.move.xml", SearchOption.AllDirectories);
                foreach (FileInfo fi in fi_decisiontrees)
                {
                    XmlDocument doc = new XmlDocument();
                    doc.Load(fi.FullName);
                    XmlNodeList moveblendparam = doc.SelectNodes(".//MoveBlendParam");
                    foreach (XmlNode n in moveblendparam)
                    {
                        if (n.Attributes["MoveBlendID"] != null)
                        {
                            String szBlendtreeName = n.Attributes["MoveBlendID"].Value.ToLower();
                            if (!blendtrees.Contains(szBlendtreeName))
                            {
                                blendtrees.Add(szBlendtreeName);
                                Console.WriteLine(szBlendtreeName);
                            }
                        }
                    }
                }
            }
            else
            {
                Console.WriteLine("Cannot find the specified file directory");
            }
            Console.Write("\nPress any key to continue... ");
            Console.ReadLine();
        }

        static void WriteAnimationReport()
        {
            CloseExcel();

            using (System.IO.StreamWriter file = new System.IO.StreamWriter(@"d:\Animation_Report.csv"))
            {
                foreach (String szAnimName in animations)
                {
                    file.WriteLine(szAnimName);
                }
            }
        }

        static void WriteP4DeleteAnimations()
        {

            DirectoryInfo di_animations = new DirectoryInfo(@"F:\Projects\wd3\main\data\animations");

            using (System.IO.StreamWriter file = new System.IO.StreamWriter(@"d:\Animation_Delete.bat"))
            {
                FileInfo[] fi_animations = di_animations.GetFiles("*.mac", SearchOption.AllDirectories);

                foreach (FileInfo fi in fi_animations)
                {
                    //
                    String relativePathAnimName = fi.FullName.Replace("F:\\Projects\\wd3\\main\\data\\", "").ToLower();
                    relativePathAnimName = relativePathAnimName.Replace(".mac", ".mab");

                    if (!animations.Contains(relativePathAnimName))
                    {
                        relativePathAnimName = relativePathAnimName.Replace("\\", "/");
                        relativePathAnimName = relativePathAnimName.Replace(".mab", ".mac");
                        file.WriteLine("p4 delete" + " //wd3-prod/main/data/" + relativePathAnimName);
                        relativePathAnimName = relativePathAnimName.Replace(".mac", ".markup");
                        file.WriteLine("p4 delete" + " //wd3-prod/main/data/" + relativePathAnimName);
                    }
                }
            }
        }

        static void WriteP4DeleteBlendtrees()
        {

            DirectoryInfo di_blendtrees = new DirectoryInfo(@"F:\Projects\wd3\main\data\move\blendtrees");

            using (System.IO.StreamWriter file = new System.IO.StreamWriter(@"d:\Blendtrees_Delete.bat"))
            {
                FileInfo[] fi_blendtrees = di_blendtrees.GetFiles("*.move.xml", SearchOption.AllDirectories);

                foreach (FileInfo fi in fi_blendtrees)
                {
                    //
                    String relativePathBlendtreeName = fi.FullName.Replace("F:\\Projects\\wd3\\main\\data\\", "").ToLower();
                    relativePathBlendtreeName = relativePathBlendtreeName.Replace(".xml", ".bin");

                    if (!blendtrees.Contains(relativePathBlendtreeName))
                    {
                        relativePathBlendtreeName = relativePathBlendtreeName.Replace("\\", "/");
                        relativePathBlendtreeName = relativePathBlendtreeName.Replace(".bin", ".xml");
                        file.WriteLine("p4 delete" + " //wd3-prod/main/data/" + relativePathBlendtreeName);
                    }
                }
            }
        }

        static void CloseExcel()
        {
            Process[] processes;
            processes = Process.GetProcessesByName("EXCEL");
            foreach (Process proc in processes)
            {
                proc.CloseMainWindow();
                proc.WaitForExit();
            }
        }


    //    static void Main(string[] args)
    //    {
    //        blendtrees = new List<string>();
    //        animations = new List<string>();

    //        datapath = @"F:\Projects\wd3\main\data";

    //        GetAnimationsFromBlendtrees(); // Get all animation in blend trees

    //        GetBlendtreesFromDecisionTrees(datapath + @"\move\decisiontrees");
    //        GetBlendtreesFromDecisionTrees(datapath + @"\move\transitions");

    //        WriteAnimationReport();
    //        WriteP4DeleteAnimations();
    //        WriteP4DeleteBlendtrees();
    //        }
    }
}