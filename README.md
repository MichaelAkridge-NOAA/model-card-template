# NOAA Model Card Template (Under Active development)
# Coming Soon - In Progress
A modern, clean template for creating model cards using Quarto & Python. This template provides a standardized way to document machine learning models following NOAA guidelines.

![Example Model Card](./assets/model_card_template_example.png)

# Coming Soon
## Features
- 📊 Clean, modern single-page layout
- 🎨 NOAA/NMFS branded design with official colors
- 📱 Responsive column layout
- 🎨 Quarto template with NOAA colors
- 🔄 Automated GitHub Actions workflow for Quarto rendering
- 📈 Support for data visualization
- 🎯 Focus on key metrics and explanations
- Metrics are displayed in dashboard-style value boxes using the provided CSS classes.


### How to Use

1. **Install Requirements:**
   - Download and install Quarto from https://quarto.org/docs/get-started/
   - Install Python dependencies:
     ```bash
     pip install -r requirements.txt jupyter
     ```
   - For PDF output:
     ```powershell
     quarto install tinytex
     ```

2. **Add your model details:**
   - Copy `model_card_template.qmd` to a new file (e.g., `my_model_card.qmd`).
   - Replace the placeholders (e.g., `{{< model_name >}}`) with your model's information.
   - Required images:
     - `nmfs-opensci-logo3.png` - NMFS OpenSci logo (download from [NOAA-NMFS-Brand-Resources](https://github.com/nmfs-opensci/NOAA-NMFS-Brand-Resources/blob/main/logos/nmfs-opensci-logo3.png))
     - `example_detection.png` - An example of your model's detection/output
     - `example_PR_curve.png` - Your model's precision-recall curve
   - Update the placeholders `{{< metric_map >}}`, `{{< metric_precision >}}`, and `{{< metric_recall >}}` with your own numbers.

3. **Render the model card:**
   ```
   # For HTML output
   quarto render my_model_card.qmd --to html
   
   # For PDF output
   quarto render my_model_card.qmd --to pdf
   ```
   The output will be in the `_output` folder.

4. **Automate with GitHub Actions:**
   - A workflow in `.github/workflows/quarto-model-card.yml` renders the Quarto template whenever `.qmd` files change or the workflow is manually run.
   - The workflow installs dependencies (including Jupyter) and then renders the template.
   - The rendered model card (HTML/PDF) is uploaded as a workflow artifact for easy download.

### Template Features
- Clean, one-page layout
- NOAA/NMFS branded design
- Automated PR curve plotting
- Support for both HTML and PDF output
- All key model card sections
- Easy to edit and extend

---

For more on Quarto, see [quarto.org](https://quarto.org/).
- https://github.com/tensorflow/model-card-toolkit
- https://modelcards.withgoogle.com/
----------
#### Disclaimer
This repository is a scientific product and is not official communication of the National Oceanic and Atmospheric Administration, or the United States Department of Commerce. All NOAA GitHub project content is provided on an ‘as is’ basis and the user assumes responsibility for its use. Any claims against the Department of Commerce or Department of Commerce bureaus stemming from the use of this GitHub project will be governed by all applicable Federal law. Any reference to specific commercial products, processes, or services by service mark, trademark, manufacturer, or otherwise, does not constitute or imply their endorsement, recommendation or favoring by the Department of Commerce. The Department of Commerce seal and logo, or the seal and logo of a DOC bureau, shall not be used in any manner to imply endorsement of any commercial product or activity by DOC or the United States Government.

#### License
- Details in the [LICENSE.md](./LICENSE.md) file.
