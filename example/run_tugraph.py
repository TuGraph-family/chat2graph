from app.plugin.tugraph.tugraph_store import get_tugraph


def main():
    """main function to demonstrate tugraph initialization and usage."""
    try:
        # get tugraph store
        store = get_tugraph()

        query = "CALL db.getLabelSchema('edge', 'HOSTILE')"
        records = store.conn.run(query)
        print(records)

        print("successfully initialized and tested tugraph")

    except Exception as e:
        print(f"main execution failed: {str(e)}")
        raise
    finally:
        if "store" in locals():
            store.conn.close()


if __name__ == "__main__":
    main()
