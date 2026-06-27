# IntelliAware Field Validation Kit — Streamlit MVP

This is the online MVP for the product design review. It demonstrates the validation workflow while manufacturer access is pending.

## What this app includes

- Product overview and validation workflow
- Trial planning checklist
- Manufacturer outreach tracker
- Ground-truth logging template
- Issue tracker with severity categories
- UI/UX test script
- Readiness handoff generator

## Fastest hosting option: Streamlit Community Cloud

1. Create a public GitHub repository.
2. Upload these files to the repository:
   - app.py
   - requirements.txt
   - data/outreach_tracker.csv
   - data/issue_tracker.csv
   - data/ground_truth_log.csv
   - data/ui_test_script.csv
   - .streamlit/config.toml
3. Go to Streamlit Community Cloud.
4. Click "Deploy an app."
5. Select the GitHub repo.
6. Set the main file path to:
   app.py
7. Deploy.
8. Copy the public streamlit.app URL into your submission slide.

## How to keep updating it

Simple version:
- Update the CSV files in GitHub.
- Streamlit redeploys the app from the repository.
- The public URL stays the same.

Better shared-team version:
- Put trackers in Google Sheets.
- Modify app.py later to read the published Google Sheet CSV links.
- This lets the team update data without editing code.

## Local preview

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Submission framing

Because manufacturer responses are still pending, this MVP is an online/lab validation workspace. It shows the full product workflow: plan trial, setup checklist, collect evidence, log issues, and generate readiness handoff. Once a manufacturer responds, factory data can be plugged into the same workflow.
