using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;

namespace AnimationReport
{
    class ActionListData
    {
        public string name, nomadID;
        public List<string> cloActionIDs = new List<string>();
        public int count;

        public void DisplayInfo()
        {
            Console.WriteLine("ActionList Name: " + name);
            Console.WriteLine("\t  NomadID: " + nomadID);
            Console.WriteLine($"\t  Count: {count}");
            Console.WriteLine("\t  CLO Action IDs: ");

            foreach (string cloActionID in cloActionIDs)
            {
                Console.WriteLine("\t\t " + cloActionID);
            }
        }
    }
}
