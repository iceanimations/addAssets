'''
Created on Oct 26, 2015

@author: qurban.ali
'''
import sys
sys.path.append("R:/Pipe_Repo/Projects/TACTIC")
import tactic_client_lib as tcl
import os
import iutil.symlinks as symlinks
from auth import user

server = None

def setServer(serv=None):
    errors = {}
    global server
    if serv: server = serv; return
    try:
        if user.user_registered():
            server = user.get_server()
        else:
            user.login('tactic', 'tactic123')
            server = user.get_server()
    except Exception as ex:
        errors['Could not connect to TACTIC'] = str(ex)
    return errors
        
def getProjects():
    errors = {}
    projects = []
    if server:
        try:
            projects = server.eval("@GET(sthpw/project.code)")
        except Exception as ex:
            errors['Could not get the list of projects'] = str(ex)
    else:
        errors['Could not find the TACTIC server'] = ''
    return projects, errors
    
        
def setProject(project):
    errors = {}
    if server:
        if project:
            try:
                server.set_project(project)
            except Exception as ex:
                errors['Could not set the project'] = str(ex)
    else:
        errors['Could not find the TACTIC server'] = ''
    return errors
        
def getEpisodes():
    eps = []
    errors = {}
    if server:
        try:
            eps = server.eval("@GET(vfx/episode.code)")
        except Exception as ex:
            errors['Could not get the list of episodes from TACTIC'] = str(ex)
    else:
        errors['Could not find the TACTIC server'] = ""
    return eps, errors
    
def getSequences(ep):
    seqs = []
    errors = {}
    if server:
        if ep:
            try:
                seqs = server.eval("@GET(vfx/sequence['episode_code', '%s'].code)"%ep)
            except Exception as ex:
                errors['Could not get the list of sequences from TACTIC'] = str(ex)
    else:
        errors['Could not find the TACTIC server'] = ""
    return seqs, errors

def getLatestFile(file1, file2):
    latest = file1
    if os.path.getmtime(file2) > os.path.getmtime(file1):
        latest = file2
    return latest
    
def getAssets(ep, seq, context='shaded/combined'):
    errors = {}
    asset_paths = {}
    if ep and seq:
        try:
            maps = symlinks.getSymlinks(server.get_base_dirs()['win32_client_repo_dir'])
        except Exception as ex:
            errors['Could not get the maps from TACTIC'] = str(ex)
        if server:
            try:
                asset_codes = server.eval("@GET(vfx/asset_in_sequence['sequence_code', '%s'].asset_code)"%seq)
            except Exception as ex:
                errors['Could not get the Sequence Assets from TACTIC'] = str(ex)
            if not asset_codes: return []
            try:
                ep_assets = server.query('vfx/asset_in_episode', filters = [('asset_code', asset_codes), ('episode_code', ep)])
            except Exception as ex:
                errors['Could not get the Episode Assets from TACTIC'] = str(ex)
            for ep_asset in ep_assets:
                try:
                    snapshot = server.get_snapshot(ep_asset, context=context, version=0, versionless=True, include_paths_dict=True)
                except Exception as ex:
                    errors['Could not get the Snapshot from TACTIC for %s'%ep_asset['asset_code']] = str(ex)
                #if not snapshot: snapshot = server.get_snapshot(ep_asset, context='shaded', version=0, versionless=True, include_paths_dict=True)
                if snapshot:
                    paths = snapshot['__paths_dict__']
                    if paths:
                        newPaths = None
                        if paths.has_key('maya'):
                            newPaths = paths['maya']
                        elif paths.has_key('main'):
                            newPaths = paths['main']
                        else:
                            errors['Could not find a Maya file for %s'%ep_asset['asset_code']] = 'No Maya or Main key found'
                        if newPaths:
                            if len(newPaths) > 1:
                                asset_paths[ep_asset['asset_code']] = symlinks.translatePath(getLatestFile(*newPaths), maps)
                            else:
                                asset_paths[ep_asset['asset_code']] = symlinks.translatePath(newPaths[0], maps)
    print asset_paths, errors
    return asset_paths, errors

if __name__ == "__main__":
    pass
    #set_server()
    #pprint(get_assets('ep09', 'EP09_SQ001'))