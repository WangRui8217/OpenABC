import argparse
import networkx as nx
import networkx.algorithms.dag as nxdag
#import dgl
import argparse,os,re
import pandas as pd
import glob
import os.path as osp
from tqdm import tqdm
import sys
from joblib import Parallel, delayed
from zipfile import ZipFile

designSet1 = ['i2c','spi','des3_area','ss_pcm','usb_phy','sasc','wb_dma','simple_spi']
designSet2 = ['dynamic_node','aes','pci','ac97_ctrl','mem_ctrl','tv80','fpu']
designSet3 = ['wb_conmax','tinyRocket','aes_xcrypt','aes_secworks']
designSet4 = ['jpeg','bp_be','ethernet','vga_lcd','picosoc']
designSet5 = ['dft','idft','fir','iir','sha256']

GML_LOC_FOLDER = '/home/wangrui/OPENABCD/graphml'
statsDataFolder = '/home/wangrui/OPENABCD/statistics'
GML_LOC = '/home/wangrui/OPENABCD/graphml'
designs = designSet1+designSet2+designSet3+designSet4+designSet5
delimiter = '\n'
commaSign = ","

#############################################################
#Node types: 0-PI, 1-PO, 2-Internal
#Gate type: 0-Unassigned, 1-NOT, 2-AND, 0-BUFF
# 0- Node type, 1- Gate type, 2- Predecessors, 3- Successors
#############################################################

informationDict = []

nodeType = {
    0: "PI",
    1: "PO",
    2: "Internal"
}

edgeType = { 1:"NOT", 0:'BUFF'}


def setGlobalAndEnvironmentVars(cmdArgs):
    global GML_LOC_FOLDER,statsDataFolder
    GML_LOC_FOLDER = cmdArgs.gml
    statsDataFolder = cmdArgs.stats



def getInformationDictForGMLFiles(gmlFileZip,desName):
    filePathName = desName+"_"+os.path.splitext(osp.basename(gmlFileZip))[0]+"_step20.bench.graphml"
    with ZipFile(gmlFileZip) as myzip:
        with myzip.open(filePathName) as myfile:
            graph = nx.read_graphml(myfile)
            synID = os.path.splitext(osp.basename(gmlFileZip))[0].split("syn")[-1]
            nodeCountDict = {"PI": 0, "PO": 0, "Internal": 0}
            edgeCountDict = {'BUFF':0,'NOT':0}
            for i, (_, feat_dict) in enumerate(graph.nodes(data=True)):
                nodeCountDict[nodeType[feat_dict['node_type']]] += 1
            for i, (_,_,feat_dict) in enumerate(graph.edges(data=True)):
                edgeCountDict[edgeType[feat_dict['edge_type']]] += 1
            longestPath = nxdag.dag_longest_path_length(graph)
            information = [int(synID),edgeCountDict["BUFF"],edgeCountDict["NOT"], nodeCountDict["Internal"], nodeCountDict["PI"],
                   nodeCountDict["PO"], longestPath]
            return information

def countGatesAndLongestPathLength(des):
    global informationDict
    aigGMLZippedFiles = glob.glob(os.path.join(GML_LOC,des,"*.zip"))
    allInfo = Parallel(n_jobs=5)(delayed(getInformationDictForGMLFiles)(zipFile,des) for zipFile in aigGMLZippedFiles)
    informationDict = allInfo


def dumpFinalGMLFileInfo(des):
    global informationDict,statsDataFolder
    finalAIGFolder = osp.join(statsDataFolder,"finalAig")
    if not osp.exists(finalAIGFolder):
        os.mkdir(finalAIGFolder)
    csvFileWrite = open(osp.join(finalAIGFolder,"processed_"+des+".csv"),'w+')
    csvFileWrite.write("sid,BUFF,NOT,AND,PI,PO,LP" + delimiter)
    for datapointList in informationDict:
        sid, BUFF, NOT, AND, PI,PO, LP = datapointList
        csvFileWrite.write(
            str(sid) + commaSign + str(BUFF) + commaSign + str(NOT) + commaSign + str(AND) + commaSign + str(PI) + commaSign + str(PO) + commaSign + str(
                LP) + delimiter)
    csvFileWrite.close()

def processDesigns(des):
    global INPUT_CSV,GML_LOC
    GML_LOC = osp.join(GML_LOC_FOLDER)
    countGatesAndLongestPathLength(des)
    dumpFinalGMLFileInfo(des)


def parseCmdLineArgs():
    parser = argparse.ArgumentParser(prog='Final AIG statistics collection', description="Circuit characteristics")
    parser.add_argument('--version',action='version', version='1.0.0')
    parser.add_argument('--gml',required=False, default='/home/wangrui/OPENABCD/graphml',help="Circuit GML folder")
    parser.add_argument('--stats',required=False,default='/home/wangrui/OPENABCD/statistics', help="Stats data folder (e.g. OPENABC_DATASET/statistics)")
    parser.add_argument('--des', required=False,default='wb_dma', help="Design Name")
    return parser.parse_args()

def main():
    # cmdArgs = parseCmdLineArgs()
    # setGlobalAndEnvironmentVars(cmdArgs)
    for design in designs:
        processDesigns(design)

if __name__ == '__main__':
    main()
