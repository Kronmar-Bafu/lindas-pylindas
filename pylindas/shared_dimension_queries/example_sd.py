from pylindas.shared_dimension_queries.shared_dimensions_queries import list_shared_dimensions, list_shared_dimension_terms, list_shared_dimensions_print, print_sparql_result

"""
Author: Fabian Cretton - HEVS

See README for an explanation
"""

def main():
    print("Shared dimensions query examples")
    print("================================")

    print("List all Shared Dimensions:")
    print("---------------------------")
    result = list_shared_dimensions("INT")
    list_shared_dimensions_print(result)

    # print("List 10 Shared Dimensions:")
    # print("--------------------------")
    # result = list_shared_dimensions("INT", "fr", 0, 10)
    # list_shared_dimensions_print(result)

    print("\nList Shared Dimensions that contains \"Canton\" in the english name")
    print("---------------------------------------------------------------")
    result = list_shared_dimensions("INT", "en", 0, 0, "Canton")
    list_shared_dimensions_print(result, "INT")

    print("\nList the Cantons shared dimension's terms")
    print("-----------------------------------------")
    result = list_shared_dimension_terms("INT", "https://ld.admin.ch/dimension/canton", "fr")
    print_sparql_result(result, ["name", "sdTerm"])

if __name__ == "__main__":
    main()
