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
    /* No extra styles needed unless Chirpy overrides it heavily */
  }

  .table-responsive .table { /* Base styles for the table itself */
    width: 100%; /* Make table try to fit its container */
    /* Default colors that will be overridden by dark mode */
    color: var(--bs-table-color, #212529); /* Default Bootstrap text */
    background-color: var(--bs-table-bg, #fff); /* Default Bootstrap bg */
    border-color: var(--bs-table-border-color, #dee2e6); /* Default Bootstrap border */
  }

  /* ----- Column Width and Text Wrapping Styles ----- */
  /* These apply in both light and dark mode */
  .table-responsive .table th,
  .table-responsive .table td {
    vertical-align: top; /* Good default */
  }

  .table-responsive .table td:nth-child(1), /* # */
  .table-responsive .table th:nth-child(1) {
    width: 3em;
    text-align: center; /* Center the rank number */
  }

  .table-responsive .table td:nth-child(2), /* Retailer */
  .table-responsive .table th:nth-child(2) {
    width: 100px; /* Or suitable fixed width */
    white-space: nowrap;
  }

  .table-responsive .table td:nth-child(3), /* Product */
  .table-responsive .table th:nth-child(3) {
    min-width: 200px; /* Adjust as needed */
    max-width: 350px; /* Adjust as needed */
    word-break: break-word;
    white-space: normal !important; /* Crucial for wrapping */
  }

  .table-responsive .table td:nth-child(4), /* Capacity (TB) */
  .table-responsive .table th:nth-child(4) {
    width: 80px; /* Or suitable fixed width */
    text-align: right;
  }

  .table-responsive .table td:nth-child(5), /* Price ($) */
  .table-responsive .table th:nth-child(5) {
    width: 90px; /* Or suitable fixed width */
    text-align: right;
  }

  .table-responsive .table td:nth-child(6), /* $/TB */
  .table-responsive .table th:nth-child(6) {
    width: 80px; /* Or suitable fixed width */
    text-align: right;
  }

  /* ----- Dark Mode Specific Table Theming ----- */
  /* Chirpy uses [data-theme="dark"] on the <html> tag */
  [data-theme="dark"] .table-responsive .table {
    /* Set Bootstrap table variables for dark mode using Chirpy variables or fallbacks */
    /* !! IMPORTANT: Replace --chirpy-text, --chirpy-card-bg, etc., with ACTUAL Chirpy variables !! */
    --bs-table-color: var(--chirpy-text-color-dark, #e0e0e0);
    --bs-table-bg: var(--chirpy-card-bg-dark, #2a2b2d);
    --bs-table-border-color: var(--chirpy-border-color-dark, #454545);
    
    /* Striped rows for dark mode */
    --bs-table-striped-color: var(--chirpy-text-color-dark, #e0e0e0);
    --bs-table-striped-bg: rgba(255, 255, 255, 0.04); /* Subtle light stripe */
                                                      
    /* Hover effect for dark mode (optional) */
    --bs-table-hover-color: var(--chirpy-text-color-dark-hover, #f0f0f0);
    --bs-table-hover-bg: rgba(255, 255, 255, 0.075);

    /* This ensures the root table text color is set based on the BS variable */
    color: var(--bs-table-color);
  }

  /* Table headers in dark mode */
  [data-theme="dark"] .table-responsive .table th {
    /* !! IMPORTANT: Replace --chirpy-text, --chirpy-header-bg etc. with ACTUAL Chirpy variables !! */
    color: var(--chirpy-header-text-color-dark, #f0f0f0);
    background-color: var(--chirpy-header-bg-dark, #343a40); 
    border-color: var(--chirpy-border-color-dark, #454545);
  }

  /* Links within the table in dark mode */
  [data-theme="dark"] .table-responsive .table a {
    /* !! IMPORTANT: Replace --chirpy-link-color-dark with ACTUAL Chirpy variable !! */
    color: var(--chirpy-link-color-dark, #6cb6ff) !important; /* !important might be needed for links */
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
