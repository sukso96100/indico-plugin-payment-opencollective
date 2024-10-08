OC_BASEURL = "https://opencollective.com"
OC_STAGING_BASEURL = "https://staging.opencollective.com"
OC_API_BASEURL = "https://api.opencollective.com/graphql/v2"
OC_GQL_ORDER_QUERY = """
query (
  $order: OrderReferenceInput!
) {
  order(order: $order) {
    id
    legacyId
    description
    amount {
      value
      currency
      valueInCents
    }
    taxAmount {
      value
      currency
      valueInCents
    }
    totalAmount {
      value
      currency
      valueInCents
    }
    quantity
    status
    frequency
    nextChargeDate
    fromAccount {
      id
      slug
      type
      name
      legalName
      description
      longDescription
      tags
      currency
      expensePolicy
      isIncognito
      createdAt
      updatedAt
      isArchived
      isFrozen
      isActive
      isHost
      isAdmin
      emails
      supportedExpenseTypes
      categories
    }
    toAccount {
      id
      slug
      type
      name
      legalName
      description
      longDescription
      tags
      currency
      expensePolicy
      isIncognito
      createdAt
      updatedAt
      isArchived
      isFrozen
      isActive
      isHost
      isAdmin
      emails
      supportedExpenseTypes
      categories
    }
    createdAt
    updatedAt
    totalDonations {
      value
      currency
      valueInCents
    }
    paymentMethod {
      id
      legacyId
      name
      service
      type
      data
      expiryDate
      createdAt
    }
    hostFeePercent
    platformTipAmount {
      value
      currency
      valueInCents
    }
    platformTipEligible
    tags
    tax {
      id
      type
      rate
      idNumber
    }
    activities {
      offset
      limit
      totalCount
    }
    data
    customData
    memo
    processedAt
    pendingContributionData {
      expectedAt
      paymentMethod
      ponumber
      memo
    }
    needsConfirmation
    comments{
      offset
      limit
      totalCount
    }
  }
}

"""