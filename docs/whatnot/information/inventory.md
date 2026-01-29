# Inventory

Inventory is the core of the Whatnot platform. It is the foundation of the Whatnot marketplace and is the primary way that sellers create and manage their products.

## Architecture

## [#](#architecture)

### Products

### [#](#products)

![Inventory Architecture](/docs/product.png)

The core of inventory can be broken down into three objects: `Product`, `ProductVariant` and `Listing`. A `Product` is the main object that represents a seller's product. A `Product` can have multiple `ProductVariant` which represent the different variations of a product. A `ProductVariant` can have multiple `Listing` which represent the different ways a product can be sold. A currently known limitation in the system is that a `ProductVariant` can only have one `Listing` at a time.

#### Product

#### [#](#product)

A `Product` holds all the information about a product such as the `title`, `description` and `images`. A `Product` makes up the core of a seller's inventory. A `Product` can have multiple `ProductVariant` which represent the different variations of a product. By default, if no options are provided, every `Product` will have a single `ProductVariant` of that product.

#### ProductVariant

#### [#](#productvariant)

A `ProductVariant` represents a variant of a product. For example, you might have a product that comes in different sizes and colors. Each size and color combination would be a `ProductVariant`. For the majority of cases, it is likely you will only have a single `ProductVariant`. A `ProductVariant` doesn't resemble the way the item is sold. That is represented by a `Listing`. Currently, a `ProductVariant` can only have one `Listing` at a time but this is likely to change in the future.

#### Listing

#### [#](#listing)

A `Listing` represents the way a product is sold. For example, a `Listing` node contains information about the price and quantity of the item that is being sold. You'll typically find listings references across the majority of the platform as they are the only way that products are sold.

### Taxonomy

### [#](#taxonomy)

![Taxonomy Architecture](/docs/taxonomy.png)

A Taxonomy node references a single line on our public taxonomy (see [our taxonomy here](https://api.whatnot.com/seller-api/rest/product-taxonomy/US.txt) ). By assigning the correct taxonomy to a product, it allows us to categorize and organize products in a way that makes sense to our buyers. Picking the right taxonomy node also impacts additional features such as attributes and filters that are discussed in the next section.

An important thing to note is that our external taxonomy is not parallel to the internal taxonomy. This means that the taxonomy node you see via the API may not resemble how your product is categorized on the public site. This is because we have a separate internal taxonomy that is used to categorize products in a way that makes sense to our buyers. We disassociate the two taxonomies to provide a layer of consistency to our API users. Each taxonomy node is binded to an internal category which will be displayed on Seller Hub.

Due to how verbose our external taxonomy is, it is likely that a lot of the taxonomy nodes are binded to the same category, and if no binding is associated with the external taxonomy node then it will be binded to the default category "And Whatnot..". If you believe that a taxonomy node is not binded to the correct category, please reach out to us and we will be able to resolve this quickly.

### Attributes

### [#](#attributes)

![Attributes Architecture](/docs/attributes.png)

Attributes are an important part of the Whatnot ecosystem. They give us a structured way to describe products. Additionally, by providing a set of attributes, it allows us to provide a consistent way to filter and search for products for our buyers.

Attributes come in several forms, such as `boolean`, `enum` and more. For some attributes, we provide a list of possible values that can be used. For example, an `enum` attribute provides values that can be used in a list.

All attributes are linked to our external taxonomy. This means that if you have a product that is in a specific taxonomy node, you will be able to provide attributes that are relevant to that taxonomy node. You can see what attributes are available for a specific taxonomy node by using the `productTaxonomyNodes` query and following it through to the `productAttributes` field.

We recommend that you provide as many attributes as possible for your products. This will allow us to provide a better experience for our buyers and will result in your products being more discoverable. We also support custom attributes which will be used when we cannot find a suitable product attribute for your product. Custom attributes will not impact the buyer experience as they are not used for filtering or searching.

Attributes may be stored and mapped within your system. However, due to the Seller API being in beta status, we **do not guarantee** that they will not change over time.

---

**Previous
- Bulk Operations**

[Imports](/docs/bulk-operations/imports)

**Next**

[schema.graphql](/docs/schemagraphql)