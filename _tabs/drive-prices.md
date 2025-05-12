---
title: HDD Price Comparison
icon: fas fa-hdd
order: 5
toc: false
---
<style>
  /* ----- Table Width and Responsiveness Styles ----- */
  .table-responsive .table td:nth-child(3), /* Product */
  .table-responsive .table th:nth-child(3) {
    min-width: 250px;
    max-width: 400px;
    word-break: break-word;
    white-space: normal !important;
  }
  .table-responsive .table td:nth-child(1), /* # */
  .table-responsive .table th:nth-child(1) { width: 3em; }
  .table-responsive .table td:nth-child(2), /* Retailer */
  .table-responsive .table th:nth-child(2) { width: 100px; white-space: nowrap; }
  .table-responsive .table td:nth-child(4), /* Capacity */
  .table-responsive .table th:nth-child(4) { width: 80px; }
  .table-responsive .table td:nth-child(5), /* Price */
  .table-responsive .table th:nth-child(5) { width: 90px; }
  .table-responsive .table td:nth-child(6), /* $/TB */
  .table-responsive .table th:nth-child(6) { width: 80px; }

  /* ----- Dark Mode Table Theming ----- */
  /* Chirpy uses [data-theme="dark"] on the <html> tag */
  [data-theme="dark"] .table-responsive .table {
    /* Set Bootstrap table variables for dark mode */
    --bs-table-color: var(--main-text-color, #e0e0e0);       /* Use Chirpy's main text color or a fallback */
    --bs-table-bg: var(--card-bg, #2a2b2d);               /* Use Chirpy's card background or a fallback */
    --bs-table-border-color: var(--main-border-color, #454545); /* Use Chirpy's border color or a fallback */
    
    /* Striped rows */
    --bs-table-striped-color: var(--main-text-color, #e0e0e0);
    --bs-table-striped-bg: rgba(255, 255, 255, 0.04); /* Subtle light stripe on dark bg */
                                                      /* Or try: var(--sidebar-bg, #1e1e1e); if you want a darker stripe */

    /* Hover effect (optional, but good for consistency) */
    --bs-table-hover-color: var(--main-text-color, #f0f0f0);
    --bs-table-hover-bg: rgba(255, 255, 255, 0.075); /* Slightly more prominent hover */

    color: var(--bs-table-color); /* Apply text color to the table itself */
  }

  /* Ensure table headers also get styled correctly */
  [data-theme="dark"] .table-responsive .table th {
    color: var(--main-text-color, #f0f0f0);
    background-color: var(--table-header-bg-dark, #343a40); /* A common dark header color */
                                                            /* Or try: var(--card-bg, #2a2b2d) if you want it same as cells */
    border-color: var(--main-border-color, #454545);
  }

  /* Ensure links within the table are styled for dark mode */
  [data-theme="dark"] .table-responsive .table a {
    color: var(--link-color-dark, #6cb6ff) !important; /* Use Chirpy's dark link color or a fallback */
  }
</style>

<!-- Rest of your Liquid code for status, table, etc. -->
<div class="mb-5">
  <em>Last Updated: {{ site.data.hdd_prices.last_updated | default: "N/A" }}</em>
  <!-- ... status Liquid ... -->
</div>

{% if site.data.hdd_prices.drives and site.data.hdd_prices.drives.size > 0 %}
  <div class="table-responsive">
    <table class="table table-striped"> <!-- Keep these classes -->
      <thead>
        <tr>
          <th class="text-center">#</th>
          <th>Retailer</th>
          <th>Product</th>
          <th class="text-right">Capacity (TB)</th>
          <th class="text-right">Price ($)</th>
          <th class="text-right">$/TB</th>
        </tr>
      </thead>
      <tbody>
        {% for item in site.data.hdd_prices.drives %}
          <tr>
            <td class="text-center">{{ forloop.index }}</td>
            <td>{{ item.Retailer }}</td>
            <td><a href="{{ item.URL }}" target="_blank" rel="noopener noreferrer">{{ item.Title | escape }}</a></td>
            <td class="text-right">{{ item.Capacity_TB }}</td>
            <td class="text-right">${{ item.Price | number_with_precision: 2, delimiter: ',' }}</td>
            <td class="text-right">${{ item.Price_per_TB | number_with_precision: 2, delimiter: ',' }}</td>
          </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>
{% else %}
  <p class="lead text-center mt-5">No drive price data currently available.</p>
{% endif %}
