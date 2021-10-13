import pandas as pd
import numpy as np
import requests

import click

from pandas.io.json import json_normalize
import json

def get_request(pure_url, api_key, version, resource, params = {}):
	headers = {
		"accept": "application/json",
		"api-key": api_key
	}	

	url = "{0}/ws/api/{1}/{2}".format(pure_url,version,resource)

	try:
		return requests.get(url, params = params, headers = headers)
	except requests.ConnectionError:
		print("Request error! {0} ({1})".format(url,params))
		return None	

def fetch_data(url, api_key, version, fields = "uuid,title.value,info.additionalExternalIds.*"):

	current = 0
	size = 50
	total = np.inf

	dfs = []

	bar = click.progressbar(length=100, label="Extracting data:", show_eta=True)

	while current < total:
		pars = {
			"fields": fields,
			"size": size,
			"offset": current
		}

		dataset = get_request(url, api_key, version, "research-outputs", pars).json()

		total = dataset['count'] 
		current = current + size

		df_title = pd.json_normalize(data=dataset['items'])

		id_column = "info.additionalExternalIds"

		if id_column not in df_title.columns:
			df_title[id_column] = None

		isnull = df_title[id_column].isnull()
		df_ids = pd.DataFrame()
		for idx, row in df_title.loc[~isnull, :].iterrows():			
			df_id = pd.json_normalize(row[id_column])
			df_id['uuid'] = row['uuid']
			df_id = df_id.set_index('uuid')
			df_ids = pd.concat([df_ids, df_id])

		df_title = df_title.drop(id_column, axis=1).set_index('uuid')

		df = pd.DataFrame()
		if df_ids.empty:
			df = df_title.copy()
		else:
			df = pd.pivot_table(df_title.join(df_ids), 
				index=['uuid','title.value'], 
				values=['value'], 
				columns=['idSource'], 
				aggfunc=';'.join)

		dfs.append(df)

		progress = np.round(current/total,2)
		bar.update(progress)

	return pd.concat(dfs)

@click.command()
@click.argument("url")
@click.argument("apikey")
@click.option("--outputfile", help = "The name of the output Excel file (must include .xlsx extension).", default = "data.xlsx")
@click.option("--apiversion", help = "The API version to use. Default: '521'", default = "521")
def main(url, apikey, outputfile, apiversion):

	click.echo("Connecting to {}.".format(url))
	data = fetch_data(url, apikey, apiversion)
	data.to_excel(outputfile)

main()
