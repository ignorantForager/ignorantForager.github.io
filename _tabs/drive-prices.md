---
title: HDD Price Comparison
icon: fas fa-hdd
order: 5
toc: false
---
<style>
  /* ----- General Table Wrapper and Base Table Styles ----- */
  .table-responsive {
    /* This Bootstrap class should handle horizontal scrolling if content overflows */
  }

  .table-responsive .table { /* Base styles for the table itself */
    width: 100%;
    /* Default light mode colors (will be overridden by dark mode) */
    color: var(--bs-table-color, #212529);
    background-color: var(--bs-table-bg, #fff);
    border-color: var(--bs-table-border-color, #dee2e6);
  }

  /* ----- Column Width and Text Wrapping Styles ----- */
  /* These apply in both light and dark mode */
  .table-responsive .table th,
  .table-responsive .table td {
    vertical-align: top;
  }

  .table-responsive .table td:nth-child(1), /* # */
  .table-responsive .table th:nth-child(1) {
    width: 3em;
    text-align: center;
  }

  .table-responsive .table td:nth-child(2), /* Retailer */
  .table-responsive .table th:nth-child(2) {
    width: 100px;
    white-space: nowrap;
  }

  .table-responsive .table td:nth-child(3), /* Product */
  .table-responsive .table th:nth-child(3) {
    min-width: 200px;
    max-width: 350px;
    word-break: break-word;
    white-space: normal !important;
  }

  .table-responsive .table td:nth-child(4), /* Capacity (TB) */
  .table-responsive .table th:nth-child(4) {
    width: 80px;
    text-align: right;
  }

  .table-responsive .table td:nth-child(5), /* Price ($) */
  .table-responsive .table th:nth-child(5) {
    width: 90px;
    text-align: right;
  }

  .table-responsive .table td:nth-child(6), /* $/TB */
  .table-responsive .table th:nth-child(6) {
    width: 80px;
    text-align: right;
  }

  /* ----- Dark Mode Specific Table Theming ----- */
  [data-theme="dark"] .table-responsive .table {
    /* Set Bootstrap table variables for dark mode using your identified Chirpy variables */
    --bs-table-color: var(--text-color, rgb(175, 176, 177));       /* Your --text-color */
    --bs-table-bg: var(--main-bg, rgb(27, 27, 30));               /* Your --main-bg (or use #2a2b2d if main-bg is too dark for table) */
    --bs-table-border-color: var(--main-border-color, rgb(44, 45, 45)); /* Your --main-border-color */
    
    /* Striped rows for dark mode */
    --bs-table-striped-color: var(--text-color, rgb(175, 176, 177));
    --bs-table-striped-bg: rgba(255, 255, 255, 0.04); /* Subtle light stripe, or try a darker version of --main-bg */
                                                      
    /* Hover effect for dark mode (optional) */
    --bs-table-hover-color: var(--text-color, rgb(200, 200, 200)); /* Slightly lighter text on hover */
    --bs-table-hover-bg: rgba(255, 255, 255, 0.075); /* Slightly more prominent hover */

    /* This ensures the root table text color is set based on the BS variable */
    color: var(--bs-table-color);
  }

  /* Table headers in dark mode */
  [data-theme="dark"] .table-responsive .table th {
    color: var(--text-color, rgb(200, 200, 200)); /* Slightly lighter/brighter for header text */
    background-color: var(--card-header-bg, #292929);  /* Your --card-header-bg */
    border-color: var(--main-border-color, rgb(44, 45, 45));
  }

  /* Links within the table in dark mode */
  [data-theme="dark"] .table-responsive .table a {
    color: var(--link-color, rgb(138, 180, 248)) !important; /* Your --link-color, !important might be needed */
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
