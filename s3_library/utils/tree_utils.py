from treelib import Tree
from collections import defaultdict
from . import helpers

def build_tree_from_s3(s3_client, bucket_name, prefix="", max_depth=None, max_items_per_level=5, show_folder_size=False):
    """
    Xây dựng cây thư mục từ S3, tối ưu lấy dữ liệu bằng `list_folders_and_files`.

    :param bucket_name: Tên bucket
    :param prefix: Prefix ban đầu
    :param max_depth: Độ sâu tối đa cần lấy
    :param max_items_per_level: Số phần tử tối đa mỗi cấp
    :return: Cây thư mục
    """
    tree = Tree()
    tree.create_node(f"📂 {bucket_name} (0 B)", "/",
                    data={"size": 0, "icon": "📂", "name": bucket_name})

    folder_sizes = defaultdict(int)  # Lưu tổng size thư mục
    # Hàng đợi BFS dạng (prefix, parent_node, depth)
    queue = [(prefix, "/", 0)]

    while queue:
        current_prefix, parent_node, depth = queue.pop(0)

        if max_depth is not None and depth >= max_depth:
            continue

        if show_folder_size:
            folders, files = helpers.list_folders_and_files(s3_client,
                                                            bucket_name, current_prefix, max_items_per_level=None)
        else:
            folders, files = helpers.list_folders_and_files(s3_client,
                                                            bucket_name, current_prefix, max_items_per_level)

        # Thêm folder vào cây
        for folder, size in folders.items():
            folder_path = f"{current_prefix}{folder}"
            node_id = folder_path.strip("/")

            if not tree.contains(node_id):
                icon = "📁"
                tree.create_node(f"{icon} {folder} (0 B)", node_id, parent=parent_node,
                                    data={"size": 0, "icon": icon, "name": folder})

            # Duyệt tiếp folder con
            queue.append((folder_path, node_id, depth + 1))

        # Thêm file vào cây
        for file_name, size in files.items():
            file_path = f"{current_prefix}{file_name}"
            node_id = file_path.strip("/")

            if not tree.contains(node_id):
                icon = "📄"
                formatted_size = helpers.human_readable_size(size)
                tree.create_node(f"{icon} {file_name} ({formatted_size})", node_id, parent=parent_node,
                                    data={"size": size, "icon": icon, "name": file_name})

            # Cập nhật size ngay vì file đã có size
            folder_sizes[parent_node] += size

    # **📌 Cập nhật lại kích thước thư mục từ dưới lên**
    for node in reversed(tree.all_nodes()):
        if tree.children(node.identifier):  # Nếu có con (là thư mục)
            total_size = sum(child.data["size"]
                                for child in tree.children(node.identifier))
            formatted_size = helpers.human_readable_size(total_size)

            node.data["icon"] = "📁"
            node.data["size"] = total_size  # Ghi lại size chính xác
            node.tag = f"{node.data['icon']} {node.data['name']} ({formatted_size})"

    return tree


def display_s3_tree(tree, node_id="/", depth=0, max_depth=3, max_items_per_level=5, prefix="", show_folder_size=False):
    """
    Hiển thị cây thư mục với giới hạn số lượng file/folder trong mỗi cấp (level),
    đồng thời căn chỉnh cột size luôn thẳng hàng và rút gọn tên dài.
    """
    max_name_length = helpers.get_max_name_length(
    tree, node_id, max_depth=max_depth)
    # Giới hạn tối đa 40 ký tự
    name_column_width = min(max_name_length, 40)
    size_column_start = 90  # Vị trí cố định cho cột size

    node = tree.get_node(node_id)
    if depth == 0:
        # In root bucket với căn chỉnh cột size
        icon = node.data["icon"]
        name = f"{node.data["name"]}/{prefix}" if prefix else node.data["name"]
        size = helpers.human_readable_size(
            node.data["size"]) if show_folder_size else ""
        formatted_name = f"{icon} {name}".ljust(size_column_start)
        print(f"{formatted_name} {size.rjust(10)}")
        prefix = ""  # Reset prefix

    if depth >= max_depth:
        return

    children = tree.children(node_id)
    folders = [c for c in children if c.data["icon"] == "📁"]
    files = [c for c in children if c.data["icon"] == "📄"]

    total_items = len(folders) + len(files)
    show_more = total_items > max_items_per_level

    if show_more:
        nodes_to_show = folders[:max_items_per_level] + \
            files[:max(0, max_items_per_level - len(folders))]
    else:
        nodes_to_show = folders + files

    last_index = len(nodes_to_show) - 1

    for i, child in enumerate(nodes_to_show):
        icon = child.data["icon"]
        name = child.data["name"]
        size = helpers.human_readable_size(child.data["size"]) if (
            icon == "📄" or show_folder_size) else ""

        # Rút gọn tên nếu quá dài
        if len(name) > name_column_width:
            name = name[:15] + "..." + name[-15:]

        is_last = (i == last_index and not show_more)
        branch = "└──" if is_last else "├──"
        new_prefix = prefix + ("    " if is_last else "│   ")

        # Đảm bảo khoảng trắng giữa tên file và cột size luôn cố định
        formatted_name = f"{prefix}{branch} {icon} {name}".ljust(
            size_column_start)
        print(f"{formatted_name} {size.rjust(10)}")

        if icon == "📁" and depth < max_depth:
            display_s3_tree(tree, node_id=child.identifier, depth=depth+1,
                        max_depth=max_depth, max_items_per_level=max_items_per_level,
                        prefix=new_prefix, show_folder_size=show_folder_size)

    if show_more:
        print(f"{prefix}└──  ...")
