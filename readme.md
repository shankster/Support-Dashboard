# Support Dashboard

This application fetches data from Freshdesk using their API and pushes it to a Geckoboard Dashboard based on an interval set in a CRON Job.

## Installation

```bash
pip install requirements.txt
```

Add your Freshdesk credentials as a environmental variable labelled `FRESHDESK_AGENT_API_KEY`. Also add your Geckoboard API key in the environment variable labelled `GECKOBOARD_API_KEY`.

Provide the list of mapping between the agent ID and their name in the following format. Mention the file name of the agent JSON in the `dashboard.py` file.
```json
{
    "235412":"Mark",
    "231442":"Jack",
    "247856":"John"
}
```

Also provide the list of mapping between the widget name in Geckoboard with their unique URL in the following format. Mention the file name of the Widget JSON in the `dashboard.py` file.
```json
{
    "open":"wd5f9cew9s-fc56w4e-56d4fdw4-x5esac58w",
    "dev_followup":"t53cew9s-fc56w4e-2qdfdas-sdsdccds23",
    "in_progress":"sw2edds-dewwef-dsq6123-wefdfdwq62"
}
```

## Contributing
Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.