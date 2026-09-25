interface AvatarProps {
  avatarUrl: string | null;
  fullName: string;
  large?: boolean;
}

export default function Avatar({ avatarUrl, fullName, large }: AvatarProps) {
  const initial = fullName.trim().charAt(0).toUpperCase();

  return (
    <span className={large ? "avatar-circle avatar-circle-lg" : "avatar-circle"}>
      {avatarUrl ? <img src={avatarUrl} alt="" /> : initial}
    </span>
  );
}
