import pandas as pd
import numpy as np
import requests

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import os
import glob

from urllib.parse import urlparse, urljoin

import click

from pandas.io.json import json_normalize
import json

def get_request(pure_url, api_key, version, resource, params = {}):
	headers = {
		"Accept": "application/json",
		"api-key": api_key
	}

	url = urljoin(pure_url, "/ws/api/{}/{}".format(version,resource)) 

	try:
		return requests.get(url, params = params, headers = headers, verify=False)
	except requests.ConnectionError:
		print("Request error! {0} ({1})".format(url,params))
		return None	

def fetch_data(url, api_key, version, family = "research-outputs", fields = "uuid,title.value,info.additionalExternalIds.*", resume = False):

	current = 0
	size = 50
	total = np.inf

	site = urlparse(url).netloc.replace(".","_")

	if resume:
		getnum = lambda x: int(x.split("/")[-1].split(".")[0])
		csv_files = glob.glob(os.path.join(site, "*.csv"))
		if csv_files:
			pages = sorted(list(map(getnum, csv_files)))
			current = pages[-1]

	bar = None

	while current < total:
		pars = {
			"fields": fields,
			"size": size,
			"offset": current
		}

		dataset = get_request(url, api_key, version, family, pars).json()

		total = dataset['count'] 
		
		if bar is None:
			bar = click.progressbar(length=total, label="Downloading data:", show_eta=True)

			click.echo("Found {} records.".format(total))

			if current > 0:
				bar.update(current)

			if current >= total:
				break

		current = current + size
		bar.update(size)

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
			df = pd.pivot_table(df_ids, 
				index=['uuid'], 
				values=['value'], 
				columns=['idSource'], 
				aggfunc=';'.join)

			df.columns = df.columns.droplevel(0)
			df = df.join(df_title)

		if not os.path.exists(site):
			os.mkdir(site)

		df.to_csv(os.path.join(site,"{}.csv".format(current)))
		
	csv_files = glob.glob(os.path.join(site, "*.csv"))

	result = pd.DataFrame()
	with click.progressbar(csv_files, label="Combining dataset...", show_eta=True) as bar:
		for csv_file in bar:
			result = pd.concat([result, pd.read_csv(csv_file, index_col="uuid")])

	output_filename = os.path.join(site, "{}.xlsx".format(site))

	click.echo("Saving output as {}...".format(output_filename))
	result.to_excel(output_filename)

@click.command()
@click.argument("url")
@click.argument("apikey")
@click.option("--apiversion", help = "The API version to use. Default: '522'", default = "522")
@click.option("--family", help = "The family to download", default = "research-outputs")
@click.option("--fields", help = "The fields to retrieve.", default = "uuid,title.value,info.additionalExternalIds.*")
@click.option("--resume", help = "Resume harvesting from last time.", default = False, is_flag=True)
def main(url, apikey, apiversion, family, fields, resume):

	click.echo("Connecting to {}.".format(url))

	data = fetch_data(url, apikey, apiversion, family, fields, resume)


main()
