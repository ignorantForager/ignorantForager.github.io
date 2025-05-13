---
title: HDD Price Report
order: 5
icon: fas fa-hdd
# No layout needed if it's just a link to an external/static HTML file.
# However, to make it a "real" tab that Chirpy processes for its navigation bar,
# you might need to make it a minimal page that redirects, or use a different linking method.

# Simpler approach: Make it an "external link" tab if Chirpy supports it directly in _tabs.
# Some themes allow 'external_url' in the front matter for tabs:
# external_url: /hdd_prices_report.html

# If external_url is not directly supported in _tabs for your Chirpy version,
# create a minimal page that redirects or just links.
# For a simple link *within* a page layout (less ideal for a main tab):
# layout: page
---

<!--
This page acts as a tab that links to the static HTML report.
Chirpy usually generates tabs from files in _tabs.
If you want this tab to directly open /hdd_prices_report.html without an intermediate page,
you'd typically configure this in _data/navigation.yml or ensure your theme handles
an 'external_url' or 'redirect' front matter in the _tabs file.

For now, let's make this page simply provide a prominent link.
-->

<p class="lead text-center mt-5">
  <a href="{{ '_pages/hdd_prices_report.html' | relative_url }}" class="btn btn-lg btn-primary">View HDD Price Report</a>
</p>

<p class="text-center text-muted">
  (This will open the self-contained report page.)
</p>

<!--
Alternative - JavaScript redirect (put this in the <head> via front matter or include if possible):
<script>
  window.location.href = "{{ '/hdd_prices_report.html' | relative_url }}";
</script>
This would make the tab click immediately redirect.
-->
