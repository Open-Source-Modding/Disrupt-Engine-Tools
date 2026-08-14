using System;
using System.Collections.Generic;
using System.Xml;
using System.IO;

namespace AnimationReport
{
    public class CLOActionData
    {
        public string name, nomadID;
        public Dictionary<string, string> moveStates = new Dictionary<string, string>();
        public List<string> anims = new List<string>();
        public List<string> props = new List<string>();
        public int actionCount, actionListCount;

        public void DisplayInfo()
        {
            //GetAnims();

            Console.WriteLine("CLO Name: " + name);
            Console.WriteLine("\tNomadID: " + nomadID);
            Console.WriteLine($"\tAction Count: {actionCount}, ActionList Count: {actionListCount}");
            Console.WriteLine("\tMoveStates: ");

            foreach (KeyValuePair<string, string> kvp in moveStates)
            {
                Console.WriteLine("\t\t " + kvp.Key + " " + kvp.Value);
            }

            Console.WriteLine("\t Anims: ");
            foreach (string anim in anims)
            {
                Console.WriteLine("\t\t" + anim);
            }

            Console.WriteLine("\t Props: ");
            foreach (string prop in props)
            {
                Console.WriteLine("\t\t" + prop);
            }
        }

        public void GetAnimPropData(Dictionary<string, string> propDict)
        {
            GetAnims();
            GetProps(propDict);
        }

        private void GetAnims()
        {
            XmlDocument doc = new XmlDocument();
            
            string prefix = @"w:\main\data\";

            if (moveStates.Count > 0)
            {
                foreach (string movestate in moveStates.Values)
                {
                    try
                    {
                        doc.Load(prefix + movestate);
                        XmlNodeList nodes = doc.SelectNodes(".//MoveBlendParam[@MoveBlendID]");

                        foreach (XmlNode node in nodes)
                        {
                            string moveBlendID = node.Attributes["MoveBlendID"].Value;
                            if (!node.Attributes["MoveBlendID"].Value.Contains("layeredprop"))
                            {
                                if (!anims.Contains(moveBlendID))
                                {
                                    doc.Load(prefix + moveBlendID.Replace("bin", "xml"));
                                    string animFile = prefix + doc.SelectSingleNode(".//AnimParam['AnimID']").Attributes["AnimID"].Value.Replace("mab", "mac");
                                    anims.Add(animFile);
                                    //Console.WriteLine(animFile + " added");
                                }
                            }
                        }
                    }
                    catch { continue; }
                }
            }
        }

        private void GetProps(Dictionary<string, string> propDict)  //Dictionary<string, string> propDict
        {
            XmlDocument doc = new XmlDocument();

            foreach (string anim in anims)
            {
                string markupFile = anim.Replace("mac", "markup");
                if (File.Exists(markupFile))
                {
                    doc.Load(markupFile);
                    XmlNodeList nodes = doc.SelectNodes(".//CPawnPropEvent");

                    foreach (XmlNode node in nodes)
                    {
                        string nomadID = node.Attributes["propPropDbName"].Value;
                        foreach (KeyValuePair<string, string> kvp in propDict)
                        {
                            if (nomadID == kvp.Key)
                            {
                                if (!props.Contains(kvp.Value))
                                {
                                    props.Add(kvp.Value);
                                }
                            }
                        }

                    } 
                }
            }
        }
    }
}
