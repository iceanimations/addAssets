'''
Created on Oct 26, 2015

@author: qurban.ali
'''
import sys
sys.path.append("R:/Pipe_Repo/Projects/TACTIC")
import tactic_client_lib as tcl
import iutil.symlinks as symlinks
from auth import user
import iutil

server = None
    
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
            if not asset_codes: return asset_paths, errors
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
                                asset_paths[ep_asset['asset_code']] = symlinks.translatePath(iutil.getLatestFile(newPaths), maps)
                            else:
                                asset_paths[ep_asset['asset_code']] = symlinks.translatePath(newPaths[0], maps)
                        else:
                            asset_paths[ep_asset['asset_code']] = None
                    else:
                        asset_paths[ep_asset['asset_code']] = None
                else:
                    asset_paths[ep_asset['asset_code']] = None
    return asset_paths, errors