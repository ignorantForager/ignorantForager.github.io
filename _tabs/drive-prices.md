---
title: HDD Price Comparison
icon: fas fa-hdd
order: 5
toc: false
---
<style>
  /* Target the "Product" column (usually the 3rd child in our table) */
  .table-responsive .table td:nth-child(3),
  .table-responsive .table th:nth-child(3) {
    min-width: 250px; /* Give it a reasonable minimum width */
    max-width: 400px; /* But also a maximum width */
    word-break: break-word; /* Allow long words/titles to break and wrap */
    white-space: normal !important; /* Ensure text wraps */
  }

  /* You might want to give other columns a fixed or max width too */
  .table-responsive .table td:nth-child(1), /* # */
  .table-responsive .table th:nth-child(1) {
    width: 3em; /* Fixed width for rank */
  }
  .table-responsive .table td:nth-child(2), /* Retailer */
  .table-responsive .table th:nth-child(2) {
    width: 100px;
    white-space: nowrap;
  }
  .table-responsive .table td:nth-child(4), /* Capacity */
  .table-responsive .table th:nth-child(4) {
    width: 80px;
  }
   .table-responsive .table td:nth-child(5), /* Price */
  .table-responsive .table th:nth-child(5) {
    width: 90px;
  }
   .table-responsive .table td:nth-child(6), /* $/TB */
  .table-responsive .table th:nth-child(6) {
    width: 80px;
  }
</style>
<div class="mb-5"> <!-- Add some margin below timestamp/status -->
  <em>Last Updated: {{ site.data.hdd_prices.last_updated | default: "N/A" }}</em>

  <div class="status-section my-3" style="font-size: 0.9em; border: 1px solid #ccc; padding: 5px 15px; border-radius: 5px; background-color: #f9f9f9;">
    <!-- Basic status display - style further as needed -->
    <strong>Scraper Status:</strong>
    <ul>
      {% for site_status in site.data.hdd_prices.scraper_status %}
        <li>{{ site_status[0] }}: {{ site_status[1].status }}
          {% if site_status[1].status == 'Success' %}
             ({{ site_status[1].count | default: 0 }} items{% if site_status[1].details %}, {{ site_status[1].details }}{% endif %})
          {% elsif site_status[1].error %}
             (Error: {{ site_status[1].error }})
          {% endif %}
        </li>
      {% endfor %}
    </ul>
    {% assign failed_count = 0 %}
    {% for site_status in site.data.hdd_prices.scraper_status %}
      {% if site_status[1].status == 'Failed' %}
         {% assign failed_count = failed_count | plus: 1 %}
      {% endif %}
    {% endfor %}
    {% if failed_count > 0 %}
      <p style="color: orange;">Note: One or more scrapers failed. Results may be incomplete.</p>
    {% endif %}
  </div>
</div>

{% if site.data.hdd_prices.drives and site.data.hdd_prices.drives.size > 0 %}
  <div class="table-responsive"> <!-- Wrapper for horizontal scrolling on small screens if needed -->
    <table class="table table-striped"> <!-- Chirpy uses Bootstrap tables, these classes should apply -->
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
