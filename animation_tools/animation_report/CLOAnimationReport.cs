using System;
using System.IO;
using System.Xml;
using System.Collections.Generic;
using Excel = Microsoft.Office.Interop.Excel;
using System.Diagnostics;
using System.Runtime.InteropServices;

namespace AnimationReport

{
    class CLOAnimationReport {

        #region Global Variable Defs
        // In Variables
        const string LONDON_LAYERS_PATH = @"W:\Main\data\Worlds\London\Objects\User";    // Level Data root folder to parse
        const string CLO_ACTIONS_PATH = @"W:\Main\data\Databases\Generic\CLOAction";                    // Data path prefix for CLO Action databases
        public static readonly string[] CLO_DB_ITEMS = new string[]{
                                                @"\LC_Filler.xml",
                                                @"\LC_Flavor.xml",
                                                @"\LC_Showcase.xml"};                                   // CLO Action Databases

        const string CLO_ACTIONLIST_PATH = @"W:\Main\data\Databases\Generic\CLOActionList.xml";

        const string MOVESTATE_PATH = @"W:\Main\data\move\DecisionTrees";
        const string PROP_DB_PATH = @"W:\Main\data\Databases\Generic\Prop.xml";

        // Out Variables
        static List<string> cloActionRefs = new List<string>();                                         // A list of all the CLO Action NomadIDs in the selected Folder(s)
        static Dictionary<string, string> cloActionAnimList = new Dictionary<string, string>();         // A dict of all the CLO Action NomadIDs and their Movestates in the selected CLOAction Databases
        static Dictionary<string, int> cloActionAnimInfo = new Dictionary<string, int>();               // A dict of the MoveStates and the amount of times they are referenced in a CLO Acton item from cloActionRefs

        #endregion

        /// <summary>
        /// Get a list of all the Level Data XML files under the root path selected in "LONDON_LAYERS_PATH"
        /// </summary>
        /// <returns>A list of the file paths for all Level Data XMLs</returns>
        public static List<FileInfo> GetLDFiles()
        {
            Console.WriteLine("Gathering a list of LD files to parse");
            List<FileInfo> fileList = new List<FileInfo>();

            DirectoryInfo dirInfo = new DirectoryInfo(LONDON_LAYERS_PATH);

            foreach (DirectoryInfo dir in dirInfo.GetDirectories())
            {
                foreach (FileInfo file in dir.GetFiles("*.xml*", SearchOption.AllDirectories)) {
                    fileList.Add(file);
                }
            }
            return fileList;
        }

        /// <summary>
        /// Get a dictionary full of all the Action Lists Nomad IDs as keys and a list of their CLO Action as the value
        /// </summary>
        /// <returns>Dictionary</returns>
        public static List<ActionListData> GetCLOActionListInfo()
        {
            Console.WriteLine("Gathering a list of CLO ActionList items from the Database");

            List<ActionListData> actionListInfo = new List<ActionListData>();

            XmlDocument actionListDoc = new XmlDocument();
            actionListDoc.Load(CLO_ACTIONLIST_PATH);
            XmlNodeList actionListNodes = actionListDoc.SelectNodes(".//Generic");

            foreach (XmlNode actionListNode in actionListNodes)
            {
                ActionListData actionListData = new ActionListData();
                actionListInfo.Add(actionListData);

                string nomadID = actionListNode.Attributes["disNomadObjectId"].Value;
                string name = actionListNode.Attributes["Name"].Value;

                actionListData.name = name;
                actionListData.nomadID = nomadID;

                foreach (XmlNode cloActionID in actionListNode.SelectNodes(".//Entry"))
                {
                    actionListData.cloActionIDs.Add(cloActionID.Attributes["cloactAction"].Value);
                }
            }
            return actionListInfo;
        }

        public static List<CLOActionData> GetCLOActionData()
        {
            Console.WriteLine("Gathering a list of CLO Actions from the Database");

            List<CLOActionData> cloDataList = new List<CLOActionData>();                                    // List to populate of all the CLO Actions in the selected databases

            foreach (string file in CLO_DB_ITEMS)
            {
                XmlDocument doc = new XmlDocument();
                doc.Load(CLO_ACTIONS_PATH + file);
                XmlNodeList nodes = doc.SelectNodes(".//Generic");

                string dbName = file.Replace("\\", null).Replace(".xml", null) + ".";

                foreach (XmlNode node in nodes)
                {
                    if (node.SelectSingleNode(".//CityLifeActionSettings").Attributes["fileMoveStateId"].Value != @"move\decisiontrees\civilians\enticers\basepose\drvr_000-000-00_5frametpose.move.bin")
                    {
                        CLOActionData cloAction = new CLOActionData();                                          // Instantiate a new CLO Action Data object
                        cloDataList.Add(cloAction);
                        string name = node.Attributes["Name"].Value;
                        string cloAnimID = node.Attributes["disNomadObjectId"].Value;
                        cloAction.name = dbName + name;
                        cloAction.nomadID = cloAnimID;
                        string moveStateID = string.Empty;
                        try
                        {
                            string loopMoveStateID = node.SelectSingleNode(".//CityLifeActionSettings").Attributes["fileMoveStateId"].Value.Replace("bin", "xml");
                            cloAction.moveStates.Add("Body: ", loopMoveStateID);

                            string entryMoveStateID = node.SelectSingleNode(".//CityLifeActionSettings").Attributes["fileEntryMoveStateId"].Value.Replace("bin", "xml");
                            cloAction.moveStates.Add("Enter: ", entryMoveStateID);

                            string exitMoveStateID = node.SelectSingleNode(".//CityLifeActionSettings").Attributes["fileExitMoveStateId"].Value.Replace("bin", "xml");
                            cloAction.moveStates.Add("Exit: ", exitMoveStateID);

                            //Console.WriteLine(moveStateID);
                        }
                        catch
                        {
                            continue;
                        }
                        //Console.WriteLine("");
                        if (moveStateID != string.Empty)
                        {
                            if (!cloActionAnimList.ContainsValue(moveStateID))
                            {
                                cloActionAnimList[cloAnimID] = moveStateID;
                            }
                        }
                    } 
                }
            }
            return cloDataList;
        }

        public static List<string> GetMoveStateFiles()
        {
            Console.WriteLine("Gathering a list of MoveState files used in the CLO Actions");

            DirectoryInfo dirInfo = new DirectoryInfo(MOVESTATE_PATH);

            List<string> moveStateFiles = new List<string>();

            foreach (DirectoryInfo dir in dirInfo.GetDirectories())
            {
                foreach (FileInfo file in dir.GetFiles("*.move.xml*", SearchOption.AllDirectories))
                {
                    moveStateFiles.Add(file.FullName);
                }
            }
            return moveStateFiles;
        }

        public static Dictionary<string, string> GetPropFiles()
        {
            Dictionary<string, string> propDict = new Dictionary<string, string>();

            XmlDocument doc = new XmlDocument();
            doc.Load(PROP_DB_PATH);
            XmlNodeList nodes = doc.SelectNodes(".//Generic");

            foreach (XmlNode node in nodes)
            {
                string name = node.Attributes["Name"].Value.Split('.')[1];
                string nomadID = node.Attributes["disNomadObjectId"].Value;

                if (!propDict.ContainsKey(nomadID))
                {
                    propDict.Add(nomadID, name);
                }
            }
            return propDict;
        }

        /// <summary>
        /// Parse the Level Data XMLs to find all CLO Objects.  If the found object
        /// is a CLO Action (not an Action List) add the NomadID value to a list
        /// </summary>        
        public static void FindCLOObjects(bool makeReport, bool showData)
        {
            List<FileInfo> fileList = GetLDFiles();
            List<ActionListData> actionListData = GetCLOActionListInfo();
            List<CLOActionData> cloList = GetCLOActionData();

            Console.WriteLine("Gathering the data on the CLOs from the selected LD files, sorting thru the data and compiling the info that you care about, kind user");

            foreach (FileInfo file in fileList)
            {
                XmlDocument doc = new XmlDocument();
                doc.Load(file.FullName);
                XmlNodeList nodes = doc.SelectNodes(".//Object[@Type='CityLifeObject']");                

                foreach (XmlNode node in nodes)
                {
                    try
                    {
                        string actionListID = node.SelectSingleNode(".//ActionSettings").Attributes["cloactlistActionList"].Value;

                        if (actionListID != null)
                        {
                            if (actionListID != "18446744073709551615")
                            {
                                ActionListData foundItem = actionListData.Find(x => x.nomadID == actionListID); //THIS IS IT! Search for a property match in a list of classes!
                                foundItem.count += 1;
                            }
                        }
                    }
                    catch
                    {
                        continue;
                    }

                    try
                    {
                        string actionID = node.SelectSingleNode(".//ActionSettings").Attributes["cloactAction"].Value;

                        if (actionID != null)
                        {
                            if (actionID != "18446744073709551615")
                            {
                                foreach (var cloActionData in cloList)
                                {
                                    if (actionID == cloActionData.nomadID)
                                    {
                                        cloActionData.actionCount = cloActionData.actionCount + 1;
                                    }
                                }
                            }
                        }
                    }
                    catch
                    {
                        continue;
                    }

                }
            }
            foreach (ActionListData actionList in actionListData)
            {
                List<string> actionsList = actionList.cloActionIDs;

                foreach (string item in actionsList)
                {
                    CLOActionData match = cloList.Find(x => x.nomadID == item);     // Find a CLO Action Data object that has a matching nomadID to the current Action List CLO nomadID
                    if (match != null)
                    {
                        match.actionListCount += actionList.count;                         
                    }
                }
            }

            // Gather the Animation File and Prop usage info for each CLO Action

            foreach (CLOActionData clo in cloList)
            {
                clo.GetAnimPropData(GetPropFiles());
                if (showData)
                {
                    clo.DisplayInfo();
                }
            }

            
            
            if (makeReport)
            {
                GenerateExcelReport(cloList);
            }
        }

        static void GenerateExcelReport(List<CLOActionData> cloList)
        {
            Stopwatch stopWatch = new Stopwatch();
            stopWatch.Start();

            
            //Get a reference to Excel and check to ensure its installed
            Excel.Application xlApp = new Microsoft.Office.Interop.Excel.Application();
            if (xlApp == null)
            {
                Console.WriteLine("Excel is not properly installed!!");
                return;
            }

            Console.WriteLine("Generating your report. Patience, please....");
            xlApp.ScreenUpdating = false;

            //Create a new Excel Workbook file
            object misValue = System.Reflection.Missing.Value;
            Excel.Workbook workbook = xlApp.Workbooks.Add(misValue);


            //Create the Worksheet
            Excel.Worksheet sheetCLOs = (Excel.Worksheet)workbook.Worksheets.get_Item(1);
            sheetCLOs.Name = "CLO Actions Info";

            // Freeze the top row
            sheetCLOs.Application.ActiveWindow.SplitRow = 1;
            sheetCLOs.Application.ActiveWindow.SplitColumn = 1;
            sheetCLOs.Application.ActiveWindow.FreezePanes = true;
            

            // Add the header
            string[] headerNames = { "CLO Name", "Nomad ID", "Action Count", "ActionList Count", "Props", "MoveStates"};
            Excel.Range rngHeader = sheetCLOs.get_Range("A1", "F1");
            rngHeader.Value2 = headerNames;
            rngHeader.Cells.Font.Bold = true;
            rngHeader.Cells.Interior.Color = Excel.XlRgbColor.rgbLightSteelBlue;
            rngHeader.AutoFilter(1);

            // Create an Animation Info worksheet and place it after the CLO Worksheet
            Excel.Worksheet sheetAnims;
            sheetAnims = (Excel.Worksheet)workbook.Worksheets.Add(misValue, (object)sheetCLOs);
            sheetAnims.Name = "CLO Animation Info";

            // Set the column counts.  TODO auto generate dat info
            int cloSheetColCount = 6;
            int animsSheetColCount = 3;

            object[,] cloDataDump = new object[cloList.Count, cloSheetColCount];
            object[,] animDataDump = new object[cloList.Count, cloSheetColCount];

            for (int i = 0; i < cloDataDump.GetLength(0); i++)
            { 
                cloDataDump[i, 0] = cloList[i].name;
                cloDataDump[i, 1] = cloList[i].nomadID;
                cloDataDump[i, 2] = cloList[i].actionCount;
                cloDataDump[i, 3] = cloList[i].actionListCount;

                // Format and write the Props to a cell
                string propList = string.Empty;
                foreach (string prop in cloList[i].props)
                {
                    if (cloList[i].props.Count == 1)
                    {
                        propList += $"{prop}";
                    }
                    else
                    {
                        propList += $"{prop}, ";
                    }
                }
                cloDataDump[i, 4] = propList;
                propList = string.Empty;

                // Format and write the Movestates to a cell
                string moveStateText = string.Empty;
                string lineBreak = "\n";
                foreach (KeyValuePair<string, string> kvp in cloList[i].moveStates)
                {
                    if (cloList[i].moveStates.Count == 1)
                    {
                        moveStateText += $"{kvp.Key} {kvp.Value}";
                    }
                    else
                    {
                        moveStateText += $"{kvp.Key} {kvp.Value}{lineBreak}";
                    }
                }
                cloDataDump[i, 5] = moveStateText;
                moveStateText = string.Empty;
            }

            Excel.Range cloDumpRange = sheetCLOs.get_Range((object)sheetCLOs.Cells[2, 1], (object)sheetCLOs.Cells[cloDataDump.GetLength(0), 6]);
            cloDumpRange.Value2 = cloDataDump;


            //For each MoveState Item add the MoveState and List of it's referenced branches to a cell
            //foreach (CLOActionData clo in cloList)
            //{
            //    string[,] cloDataDump = new string[cloList.Count, 6];

            //    for (int i = 0; i < cloDataDump.GetLength(0); i++)
            //    {
            //        cloDataDump[i,0] = clo.name;
            //        Console.WriteLine(cloDataDump[i, 0].ToString() + " array val added");
            //    }


            ////Add in MoveState 
            //sheetCLOs.Cells[cloSheetRow, 1].Value2 = clo.name;
            //sheetCLOs.Cells[cloSheetRow, 2].Value2 = clo.nomadID;
            //sheetCLOs.Cells[cloSheetRow, 3].Value2 = clo.actionCount;
            //sheetCLOs.Cells[cloSheetRow, 4].Value2 = clo.actionListCount;




            //cloSheetRow++;

            //// Write animation files and their total ussage counts to a row
            //foreach (string anim in clo.anims)
            //{
            //    sheetAnims.Cells[cloSheetRow, 1].Value2 = anim;
            //    sheetAnims.Cells[cloSheetRow, 2].Value2 = clo.actionCount + clo.actionListCount;
            //}
            //animSheetColumn = 1;
            //animSheetRow++;

            sheetCLOs.Columns.AutoFit();
            sheetAnims.Columns.AutoFit();
            sheetCLOs.Rows.RowHeight = 15;
            sheetCLOs.Columns[5].ColumnWidth = 50;
            sheetCLOs.Columns[6].ColumnWidth = 200;

            sheetCLOs.Columns[3].Cells.HorizontalAlignment =
                 Microsoft.Office.Interop.Excel.XlHAlign.xlHAlignCenter;
            sheetCLOs.Columns[4].Cells.HorizontalAlignment =
                 Microsoft.Office.Interop.Excel.XlHAlign.xlHAlignCenter;

            //Save the file and close the Excel application processes
            xlApp.ScreenUpdating = true;
            xlApp.DisplayAlerts = false;
            workbook.SaveAs(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\CLOAnimationReport.xls", Excel.XlFileFormat.xlWorkbookNormal);
            workbook.Close(true, misValue, misValue);
            xlApp.Workbooks.Open(@"C:\Users\sdiehl\Documents\Scripts\OutputFiles\CLOAnimationReport.xls");
            xlApp.DisplayAlerts = true;
            xlApp.Visible = true;
            //xlApp.Quit();    

            //Marshal.ReleaseComObject(workbook);
            //Marshal.ReleaseComObject(xlApp);

            stopWatch.Stop();
            TimeSpan ts = stopWatch.Elapsed;
            Console.WriteLine(ts + " for Excel");
        }

    }
}
