import pandas as pd
import numpy as np
import requests

from pandas.io.json import json_normalize
import json

pure_url = "https://<SITE>.pure.elsevier.com"
api_key = "<API_KEY>"
pure_api_url = "{}/ws/api/521/".format(pure_url)
fields = "uuid,title.value,info.additionalExternalIds.*"

def get_request(resource, params = {}):
	headers = {
		"accept": "application/json",
		"api-key": api_key
	}	
	try:
		return requests.get(
			"{}{}".format(pure_api_url, resource), 
			params = params, 
			headers = headers
		)
	except requests.ConnectionError:
		print("Request error! {0} ({1})".format(pure_api_url,params))
		return None	

current = 0
size = 50
total = np.inf

dfs = []

while current < total:

	pars = {
		"fields": fields,
		"size": size,
		"offset": current
	}

	dataset = get_request("research-outputs", pars).json()

	total = dataset['count'] 
	current = current+size
	print("{0}%".format( np.round(current / total * 100 , 2)))

	df_title = pd.json_normalize(data=dataset['items'])

	id_column = "info.additionalExternalIds"

	if id_column not in df_title.columns:
		df[id_column] = None
	isnull = df_title[id_column].isnull()
	df_ids = pd.DataFrame()
	for idx, row in df_title.loc[~isnull, :].iterrows():			
		df_id = pd.json_normalize(row[id_column])
		df_id['uuid'] = row['uuid']
		df_id = df_id.set_index('uuid')
		df_ids = pd.concat([df_ids, df_id])

	df_title = df_title.drop(id_column, axis=1).set_index('uuid')

	df = pd.pivot_table(df_title.join(df_ids), 
		index=['uuid','title.value'], 
		values=['value'], 
		columns=['idSource'], 
		aggfunc=';'.join)

	dfs.append(df)


out_df = pd.concat(dfs)
out_df.to_excel("ids.xlsx")