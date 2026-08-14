using System;
using System.Collections.Generic;
using System.IO;
using System.Xml;
using Excel = Microsoft.Office.Interop.Excel;
using System.Diagnostics;


namespace AnimationReport
{
    class AnimationReport
    {
        const String PATH_DECISION_TREE = @"F:\Projects\WD3\Main\data\move\DecisionTrees";

        static List<String> moveStates;
        static List<FileInfo> moveStateFiles;
        
        public static void XMLTest()
        {
            XmlDocument doc = new XmlDocument();
            doc.Load(@"W:\Main\data\move\DecisionTrees\Player-Ai\locomotion\Drvr_Locomotion_Emote.move.xml");
            XmlNodeList nodes = doc.SelectNodes(".//ChildNode");
            Console.WriteLine("go time");

            foreach (XmlNode node in nodes)
            {
                Console.WriteLine("ClassName: " + node.Attributes["hid_DTCTH_ClassName"].Value);
                Console.WriteLine("\tLocalName: " + node.Attributes["LocalName"].Value);
                Console.WriteLine("\tPath: " + node.Attributes["NodeID"].Value);
                Console.WriteLine();
            }
            Console.ReadLine();
        }

        public static void GetMoveStates(bool makeReport = false)
        {
            if (makeReport)
            {
                using (System.IO.StreamWriter fs = new System.IO.StreamWriter(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\movestates.txt"))
                {
                    DirectoryInfo dirInfo = new DirectoryInfo(PATH_DECISION_TREE);

                    foreach (DirectoryInfo dir in dirInfo.GetDirectories())
                    {
                        Console.WriteLine(dir.FullName + " added");
                        fs.WriteLine(dir.FullName);
                        foreach (FileInfo file in dir.GetFiles("*.*", SearchOption.AllDirectories))
                        {
                            Console.WriteLine("  " + file.Name + " added");
                            fs.WriteLine("  " + file.Name.Replace(".move.xml", ""));
                        }
                    }
                }
            }

            else
            {
                DirectoryInfo dirInfo = new DirectoryInfo(PATH_DECISION_TREE);
                moveStates = new List<string>();
                moveStateFiles = new List<FileInfo>();

                foreach (DirectoryInfo dir in dirInfo.GetDirectories())
                {
                    foreach (FileInfo file in dir.GetFiles("*.move.xml*", SearchOption.AllDirectories))
                    {
                        if (!moveStates.Contains(file.FullName))
                        {
                            moveStates.Add(file.FullName);
                            moveStateFiles.Add(file);
                            //Console.WriteLine(file.FullName);
                        }
                    }
                }
            }
            Console.WriteLine("\nDONE!  Press 'Enter' to exit");
            Console.ReadLine();
        }

        /// <summary>
        /// Iterate thru the MoveState files to find all MoveStates that are MoveState references
        /// Collect them and all the branches that reference them
        /// </summary>
        /// <param name="makeReport">If you want to write out a .txt file with the results</param>
        /// <returns></returns>
        private static Dictionary<string, List<string>> GetStateRefs(bool makeReport = false)
        {
            Dictionary<string, List<string>> stateRefDict = new Dictionary<string, List<string>>();

            DirectoryInfo dirInfo = new DirectoryInfo(PATH_DECISION_TREE);
            foreach (DirectoryInfo dir in dirInfo.GetDirectories())
            {
                foreach (FileInfo file in dir.GetFiles("*.move.xml*", SearchOption.AllDirectories))
                {
                    XmlDocument doc = new XmlDocument();
                    doc.Load(file.FullName);
                    XmlNodeList nodes = doc.SelectNodes(".//ChildNode[@UniqueID]");

                    foreach (XmlNode node in nodes)
                    {
                        if (node.Attributes["hid_DTCTH_ClassName"] != null)
                        {
                            string itemType = node.Attributes["hid_DTCTH_ClassName"].Value;

                            if (itemType == "CMoveStateRef")
                            {
                                string state = node.SelectSingleNode(".//MoveStateParam").Attributes["MoveStateID"].Value;
                                //Console.WriteLine("State: " + state);
                                string branch = node.Attributes["NodeID"].Value;
                                //Console.WriteLine("Branch: " + branch);

                                if (stateRefDict.ContainsKey(state))
                                {
                                    stateRefDict[state].Add(branch);
                                }
                                else
                                {
                                    stateRefDict.Add(state, new List<string>());
                                    stateRefDict[state].Add(branch);
                                }
                            }
                        }
                    }
                }
            }

            if (makeReport)     //Write out a report if desired
            {
                using (System.IO.StreamWriter fs = new System.IO.StreamWriter(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\MoveState_RefList.txt"))
                {
                    foreach (KeyValuePair<string, List<string>> pair in GetStateRefs())
                    {
                        fs.WriteLine("Referenced State: " + pair.Key);
                        fs.WriteLine("\tBranches: ");
                        foreach (string branch in pair.Value)
                        {
                            fs.WriteLine("\t\t" + branch);
                        }
                        fs.WriteLine("");
                    }
                }
            }
            return stateRefDict;
        }

        /// <summary>
        /// Create an Excel file with the referenced MoveStates and their branches
        /// </summary>
        static void GenerateExcelReport()
        {
            //Get a reference to Excel and check to ensure its installed
            Excel.Application xlApp = new Microsoft.Office.Interop.Excel.Application();
            if (xlApp == null)
            {
                Console.WriteLine("Excel is not properly installed!!");
                return;
            }

            Console.WriteLine("Generating your report. Patience, please....");
            //Get the list of Move State References and their Referenced Branches
            Dictionary<string, List<string>> stateRefList = new Dictionary<string, List<string>>();
            stateRefList = GetStateRefs();

            //Create a new Excel Workbool file
            object misValue = System.Reflection.Missing.Value;
            Excel.Workbook xlWorkBook = xlApp.Workbooks.Add(misValue);

            //Create the headers
            Excel.Worksheet xlWorkSheet = (Excel.Worksheet)xlWorkBook.Worksheets.get_Item(1);
            xlWorkSheet.Columns.ColumnWidth += 100;
            xlWorkSheet.Cells[1, 1].Font.Bold = true;
            xlWorkSheet.Cells[1, 1] = "Referenced State";
            xlWorkSheet.Cells[1, 1].Interior.Color = Excel.XlRgbColor.rgbLightSteelBlue;
            xlWorkSheet.Cells[1, 2].Font.Bold = true;
            xlWorkSheet.Cells[1, 2] = "Branch";
            xlWorkSheet.Cells[1, 2].Interior.Color = Excel.XlRgbColor.rgbLightSteelBlue;

            //Set the start row, column to iterate on from
            int column = 1;
            int row = 2;

            //For each MoveState Item add the MoveState and List of it's referenced branches to a cell
            foreach (string key in stateRefList.Keys)
            {
                //Add in MoveState 
                xlWorkSheet.Cells[row, column].Value = key;
                foreach (string value in stateRefList[key])
                {
                    // Set the column and add the branches to cells
                    column = 2;
                    if (stateRefList[key].Count != 1)
                    {
                    row++;
                    }
                    xlWorkSheet.Cells[row, column].Value = value;                   
                }
                //Reset the column to 1 and increment the row
                column = 1;
                row++;                
            }

            //Save the file and close the Excel application processes
            xlApp.DisplayAlerts = false;
            xlWorkBook.SaveAs(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\MoveState_RefList.xls", Excel.XlFileFormat.xlWorkbookNormal);
            xlWorkBook.Close(true, misValue, misValue);
            xlApp.Workbooks.Open(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\MoveState_RefList.xls");
            xlApp.DisplayAlerts = true;
            xlApp.Visible = true;
            //xlApp.Quit();            
        }

        
        static void Main(string[] args)
        {
            Stopwatch stopWatch = new Stopwatch();
            stopWatch.Start();

            //ExcelTest.Test();

            CLOAnimationReport.FindCLOObjects(true, false);          

            stopWatch.Stop();
            TimeSpan ts = stopWatch.Elapsed;
            Console.WriteLine(ts);

            Console.WriteLine("Done");
            Console.ReadLine();
        }
    }
}
