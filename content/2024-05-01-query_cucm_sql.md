Title: Querying CUCM Database using SQL
Date: 2024-05-01
Category: networking
Tags: cisco,cucm,sql,api,postman

## Exploring Cisco Unity Call Manager (CUCM) Database Access via Postman and SOAP/AXL API

Delving into the intricacies of Cisco Unity Call Manager (CUCM) database access via Postman and SOAP/AXL API opens up a realm of possibilities. While this won’t serve as a step-by-step guide, consider it a tour through a few essential examples, primarily focusing on leveraging custom SQL queries within Postman requests.

If SQL isn’t in your skill set, this isn’t the tutorial where you’ll find comprehensive lessons. I’m no SQL guru myself, having only dabbled in it sparingly. Below, I’ll showcase a few examples of what I’ve managed to achieve with my modest understanding.

### Querying End Users

To retrieve comprehensive details of a specific end user from the `enduser` table, the following snippet can be employed within the Postman request body. Simply substitute `xxxxx` in the SQL query’s last line with the target user’s username.

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.cisco.com/AXL/API/14.0">
<soapenv:Header />
<soapenv:Body>
    <ns:executeSQLQuery>
        <sql>
            SELECT *
            FROM enduser
            WHERE userid = 'xxxxx'
        </sql>
    </ns:executeSQLQuery>
</soapenv:Body>
</soapenv:Envelope>
```

### Querying End Users and Their Associated Groups

This query is slightly more intricate but yields essential information about a user’s Primary Key ID (PKID) and the Foreign Key (FK) of the group(s) they belong to. Similar to the previous example, substitute `xxxxx` with the target user’s ID.

```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:ns="http://www.cisco.com/AXL/API/14.0">
<soapenv:Header />
<soapenv:Body>
    <ns:executeSQLQuery>
        <sql>
            SELECT e.pkid, m.fkdirgroup
            FROM enduserdirgroupmap AS m
            INNER JOIN enduser AS e ON m.fkenduser = e.pkid
            WHERE e.userid = 'xxxxx'
        </sql>
    </ns:executeSQLQuery>
</soapenv:Body>
</soapenv:Envelope>
```

### Conclusion

Exploring the capabilities of Cisco Unity Call Manager’s database through Postman and SQL queries unveils a world of administrative potential. While these examples offer a glimpse into its functionality, mastering these techniques can significantly amplify one’s ability to manage and optimize Cisco’s ecosystem efficiently.

Whether you’re a seasoned administrator seeking to streamline operations or an enthusiast eager to dive into the intricacies of CUCM, leveraging Postman and SQL queries provides a powerful toolkit. With continued exploration and practice, you’ll unlock even greater insights and efficiencies within your Cisco infrastructure.

