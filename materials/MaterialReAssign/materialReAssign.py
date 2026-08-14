import csv
import subprocess
import argparse

list=[]
force=False
switchBack=False
# filePath='D:\WD2GlassConversion\DerivationsMade\\'

# -----------Args------------------------
parser = argparse.ArgumentParser(description='Process material derivations')
parser.add_argument('csvReference', help='path of the reference MatList_ file')
parser.add_argument('force', help='force write to file')
parser.add_argument('switchBack', help='force write to file')


# parser.add_argument('params', nargs='*', help='parameters to send to child')

args = parser.parse_args()
csvReference = args.csvReference

if args.force == "force":
    force=True
if args.switchBack == 'switchBack':
    switchBack=True
# csvReference='MatList_Derivations_LargeBuildings.csv'

def openFile(filename):
    print "\n", subprocess.check_output('p4 edit ' + filename)


def readFile(filePath):
    with open(filePath, 'r') as input:
        inputFilters = csv.DictReader(input)
        duplicate = False
        for all in inputFilters:
            list.append(all)

def process():
    for all in list:

        # Force Adding both the gamex/glm and the xml files in perforce
        if force:
            openFile(all['Asset'])
            temp = str(all['Asset'])
            if '.gamex' in temp:
                temp = temp.replace('.gamex','.xml')
            else:
                if '.glm' in temp:
                    temp = temp.replace('.glm','.xml')
            openFile(temp)
            print ">>>FORCE ADDED FILES TO PERFORCE"

        print "\n-----Conversion process began:", all
        if switchBack:
            print '\nT:\\rpatel\Debug\COM_ReplaceGeoMat.exe -f -single "' + all['Asset'] + '" "' + all['CurrentMat'] + '" "' + all['NewMat'] + '"\n'
            print "\n", subprocess.check_output('T:\\rpatel\Debug\COM_ReplaceGeoMat.exe -f -single "' + all['Asset'] + '" "' + all['NewMat'] + '" "' + all['CurrentMat'] + '"', shell=True)
        else:
            print '\nT:\\rpatel\Debug\COM_ReplaceGeoMat.exe -f -single "'+all['Asset']+'" "'+all['CurrentMat']+'" "'+all['NewMat']+ '"\n'
            print "\n", subprocess.check_output('T:\\rpatel\Debug\COM_ReplaceGeoMat.exe -f -single "'+all['Asset']+'" "'+all['CurrentMat']+'" "'+all['NewMat']+ '"', shell=True)
        # print "\n", subprocess.check_output('\\\\ubisoft.org\projects\Orwell\TOR\Public\sjennings\Tools-WIP\COM_REplaceGeoMat\COM_ReplaceGeoMat.exe -f -single "'+all['Asset']+'" "'+all['ID']+'" "'+all['ID']+ '"', shell=True)
        print "Conversion Complete--------------------------------------------------------"

def main ():
    print "Filename input:", csvReference
    readFile('.\\'+csvReference)
    process()

if '__name__':
    main()