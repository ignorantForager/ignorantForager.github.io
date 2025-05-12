---
title: HDD Price Comparison
icon: fas fa-hdd
order: 5
toc: false
---
<style>
  /* ----- General Table Wrapper and Base Table Styles ----- */
  .table-responsive {
    /* Bootstrap class for horizontal scrolling */
  }

  .table-responsive .table {
    width: 100%;
    /* Default light mode Bootstrap variables will be used by default.
       Dark mode overrides these using Chirpy's variables. */
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
  /* Chirpy uses [data-theme="dark"] on the <html> tag */

  /* Target the table and set general dark mode properties */
  [data-theme="dark"] .table-responsive .table {
    color: var(--text-color); /* rgb(175, 176, 177) */
    border-color: var(--tb-border-color); /* var(--tb-odd-bg) which is rgb(31, 31, 34) */
    /* General background for the table if needed, though rows will override */
    /* background-color: var(--main-bg); */
  }

  /* Table Headers in dark mode */
  [data-theme="dark"] .table-responsive .table th {
    color: var(--text-color); /* Or a slightly brighter version if needed */
    background-color: var(--card-header-bg, #292929); /* Your identified header bg, or var(--main-bg) */
    border-color: var(--tb-border-color);
  }

  /* Table Body Rows in dark mode - using Chirpy's table variables! */
  [data-theme="dark"] .table-responsive .table tbody tr {
    /* Default row background will be the general table bg or inherited */
  }
  
  /* Odd rows for striping - use Chirpy's --tb-odd-bg */
  [data-theme="dark"] .table-responsive .table.table-striped > tbody > tr:nth-of-type(odd) > * {
    background-color: var(--tb-odd-bg); /* rgb(31, 31, 34) */
    color: var(--text-color);
  }
  
  /* Even rows for striping - use Chirpy's --tb-even-bg (if different from default cell)*/
  /* Bootstrap default for striped tables is that even rows take the normal table cell bg */
  /* If --tb-even-bg is the same as the default table cell background, you might not need this explicit rule */
  [data-theme="dark"] .table-responsive .table.table-striped > tbody > tr:nth-of-type(even) > * {
     background-color: var(--tb-even-bg); /* rgb(27, 27, 30) */
     color: var(--text-color);
  }

  /* Hover effect for table rows in dark mode */
  [data-theme="dark"] .table-responsive .table tbody tr:hover > * {
    background-color: var(--tb-hover-bg); /* rgb(45, 56, 62) */
    color: var(--text-color); /* Or a slightly brighter hover text color */
  }

  /* Links within the table in dark mode */
  [data-theme="dark"] .table-responsive .table a {
    color: var(--link-color) !important; /* rgb(138, 180, 248) */
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
