"""Parallel-job entry point; only scoped computed results can pass."""
from pathlib import Path
import sys,json,subprocess,hashlib
H=Path(__file__).resolve().parent
branches={
 'compression':(['compress_characters.py','verify_compression.py'],['CHARACTER_COMPRESSION_CERTIFICATE.json','INDEPENDENT_COMPRESSION_VERIFICATION.json','COMPRESSED_SPATIAL_FACTOR.json.gz']),
 'network':(['analyze_network.py','verify_network.py'],['ALL_FACTOR_NETWORK_ANALYSIS.json','INDEPENDENT_NETWORK_VERIFICATION.json']),
 'partition':(['certify_partition.py','verify_partition_independent.py'],['ALL_24_VACUUM_GRAM_ENCLOSURE.json','INDEPENDENT_PARTITION_VERIFICATION.json'])}
def main():
    job=sys.argv[1];scripts,files=branches[job];d=H/job
    for s in scripts:subprocess.run([sys.executable,str(d/s)],cwd=H,check=True)
    out={'status':'PASS_SCOPED_'+job.upper(),'branch':job,'full_coupled_Gram_contracted':False,'files':[{'path':job+'/'+f,'sha256':hashlib.sha256((d/f).read_bytes()).hexdigest(),'bytes':(d/f).stat().st_size} for f in files]}
    (d/'EXECUTION_MANIFEST.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
if __name__=='__main__':main()
